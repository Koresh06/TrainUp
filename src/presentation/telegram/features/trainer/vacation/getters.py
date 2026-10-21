from datetime import date, timedelta
from html import escape

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.booking.get_views import GetBookingViewsRequest
from src.application.use_cases.vacation.manage import GetVacationsRequest
from src.application.use_cases.vacation.preview import (
    PreviewVacationRequest,
    VacationPreviewDTO,
)
from src.domain.constants import CALENDAR_BUFFER_DAYS
from src.domain.entities.trainer_vacation import TrainerVacation
from src.domain.enums.booking import ACTIVE_BOOKING_STATUSES
from src.domain.repositories.booking import BookingView
from src.domain.utils import get_project_today
from src.presentation.telegram.common.booking_labels import short_day
from src.presentation.telegram.widgets.booking_calendar import (
    BUSY_DAYS_CACHE_KEY,
    HORIZON_CACHE_KEY,
)


def period_label(date_from: date, date_to: date) -> str:
    if date_from == date_to:
        return short_day(date_from)
    return f"{short_day(date_from)} – {short_day(date_to)}"


@inject
async def vacations_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    vacations: list[TrainerVacation] = await mediator.handle(
        GetVacationsRequest(trainer_id=dialog_manager.start_data["trainer_id"])
    )
    today = get_project_today()
    return {
        "vacations": [
            {
                "id": str(v.id),
                "label": ("🏖 сейчас · " if v.covers(today) else "🏖 ")
                + period_label(v.date_from, v.date_to),
            }
            for v in vacations
        ],
        "empty_hint": "" if vacations else "\n\nЗапланированных периодов нет.",
    }


@inject
async def pick_calendar_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    today = get_project_today()
    views: list[BookingView] = await mediator.handle(
        GetBookingViewsRequest(
            trainer_id=trainer_id,
            date_from=today,
            date_to=today + timedelta(days=CALENDAR_BUFFER_DAYS),
            statuses=ACTIVE_BOOKING_STATUSES,
        )
    )
    busy: dict[str, int] = {}
    for v in views:
        busy[v.slot_date.isoformat()] = busy.get(v.slot_date.isoformat(), 0) + 1
    dialog_manager.dialog_data[BUSY_DAYS_CACHE_KEY] = busy
    dialog_manager.dialog_data[HORIZON_CACHE_KEY] = CALENDAR_BUFFER_DAYS
    raw_from = dialog_manager.dialog_data.get("date_from")
    return {"date_from": short_day(date.fromisoformat(raw_from)) if raw_from else ""}


@inject
async def preview_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    date_from = date.fromisoformat(dialog_manager.dialog_data["date_from"])
    date_to = date.fromisoformat(dialog_manager.dialog_data["date_to"])
    preview: VacationPreviewDTO = await mediator.handle(
        PreviewVacationRequest(
            trainer_id=dialog_manager.start_data["trainer_id"],
            date_from=date_from,
            date_to=date_to,
        )
    )
    lines = [
        f"🏖 <b>{period_label(date_from, date_to)}</b>",
        "",
        f"🔒 Закроется слотов: {preview.slots_to_block}",
        f"❌ Отменится записей: {len(preview.bookings)}",
    ]
    if preview.bookings:
        lines.append("Клиенты в Telegram получат сообщение, что вы в отпуске.")
    if preview.offline_clients:
        lines.append(
            "📵 Предупредите сами: " + ", ".join(escape(n) for n in preview.offline_clients)
        )
    lines.append("\nСлоты, которые появятся в этом периоде позже, тоже будут закрыты.")
    return {"text": "\n".join(lines)}


async def done_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    return {"text": dialog_manager.dialog_data.get("done_text", "Готово")}


@inject
async def detail_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    vacations: list[TrainerVacation] = await mediator.handle(
        GetVacationsRequest(trainer_id=dialog_manager.start_data["trainer_id"])
    )
    vacation = next(v for v in vacations if v.id == dialog_manager.dialog_data["vacation_id"])
    return {"period": period_label(vacation.date_from, vacation.date_to)}
