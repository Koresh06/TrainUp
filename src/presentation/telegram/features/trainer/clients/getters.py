from datetime import date
from html import escape

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.booking.get_views import GetBookingViewsRequest
from src.application.use_cases.calendar.get_day_availability_map import (
    GetDayAvailabilityMapRequest,
)
from src.application.use_cases.calendar.get_slot_by_id import GetSlotByIdRequest
from src.application.use_cases.client.get_answers_by_id import GetClientAnswersRequest
from src.application.use_cases.client.get_by_id import GetClientByIdRequest
from src.application.use_cases.client.get_clients_by_trainer import (
    GetClientsByTrainerIdRequest,
)
from src.application.use_cases.recurring_booking.get_all_active_by_trainer import (
    GetActiveRecurringBookingsByTrainerRequest,
)
from src.application.use_cases.registration_questions.get_all import (
    GetAllRegistrationQuestionsRequest,
)
from src.core.config import settings
from src.application.use_cases.client._shared import CLIENT_INVITE_PREFIX
from src.domain.constants import CALENDAR_BUFFER_DAYS
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.client import Client
from src.domain.entities.client_answer import ClientAnswer
from src.domain.entities.recurring_booking import RecurringBooking
from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.enums.booking import ACTIVE_BOOKING_STATUSES, BookingStatus
from src.domain.enums.client import ClientEditableField
from src.domain.enums.training import SPORT_EXPERIENCE_LABELS
from src.domain.repositories.booking import BookingView
from src.domain.utils import get_project_today
from src.presentation.telegram.common.booking_labels import (
    STATUS_ICONS,
    WEEKDAY_SHORT,
    short_day,
)
from src.presentation.telegram.common.free_slots import free_slot_options
from src.presentation.telegram.widgets.booking_calendar import (
    AVAILABILITY_CACHE_KEY,
    HORIZON_CACHE_KEY,
)

UPCOMING_IN_CARD = 5

EDIT_FIELD_PROMPTS: dict[ClientEditableField, str] = {
    ClientEditableField.FIRST_NAME: "Введите имя клиента:",
    ClientEditableField.LAST_NAME: "Введите фамилию клиента:",
    ClientEditableField.PHONE: "Введите телефон клиента:",
    ClientEditableField.TRAINER_NOTE: (
        "Введите заметку о клиенте — её видите только вы\n"
        "(например: «колено, без прыжков», «оплачивает переводом»):"
    ),
}


@inject
async def clients_list_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    clients: list[Client] = await mediator.handle(
        GetClientsByTrainerIdRequest(trainer_id=trainer_id)
    )
    recurring: list[RecurringBooking] = await mediator.handle(
        GetActiveRecurringBookingsByTrainerRequest(trainer_id=trainer_id)
    )
    recurring_ids = {r.client_id for r in recurring}

    items = []
    for c in clients:
        label = c.full_name
        if c.id in recurring_ids:
            label += " 🔁"
        if not c.has_telegram:
            label = f"📵 {label}"
        items.append({"id": str(c.id), "label": label})

    offline = sum(1 for c in clients if not c.has_telegram)
    summary = f"Всего: {len(clients)}"
    if offline:
        summary += f" · без Telegram 📵: {offline}"
    return {
        "clients": items,
        "summary": summary if clients else "Клиентов пока нет — пригласите по ссылке или добавьте вручную.",
    }


def _contacts(client: Client) -> str:
    lines = []
    if client.has_telegram:
        lines.append(f'💬 <a href="tg://user?id={client.tg_id}">Написать в Telegram</a>')
        if client.username:
            lines.append(f"👤 @{escape(client.username)}")
    else:
        lines.append("📵 Без Telegram — уведомления не получает")
    lines.append(f"📞 {escape(client.phone) if client.phone else '—'}")
    return "\n".join(lines)


async def _client_card_lines(
    mediator: Mediator, trainer_id: int, client: Client
) -> list[str]:
    today = get_project_today()
    views: list[BookingView] = await mediator.handle(
        GetBookingViewsRequest(trainer_id=trainer_id, client_id=client.id)
    )
    upcoming = [
        v for v in views if v.booking.status in ACTIVE_BOOKING_STATUSES and v.slot_date >= today
    ]
    completed = [v for v in views if v.booking.status == BookingStatus.COMPLETED]
    cancelled = sum(1 for v in views if v.booking.status == BookingStatus.CANCELLED)

    lines = []
    if upcoming:
        lines.append("📅 <b>Ближайшие:</b>")
        for v in upcoming[:UPCOMING_IN_CARD]:
            lines.append(
                f"  {STATUS_ICONS.get(v.booking.status, '')} {short_day(v.slot_date)} "
                f"{v.start_time.strftime('%H:%M')}"
                f"{' 🔁' if v.booking.recurring_booking_id else ''}"
            )
        if len(upcoming) > UPCOMING_IN_CARD:
            lines.append(f"  … и ещё {len(upcoming) - UPCOMING_IN_CARD}")
    else:
        lines.append("📅 Будущих записей нет")

    stats = f"📊 Проведено: {len(completed)} · отмен: {cancelled}"
    if completed:
        last: date = max(v.slot_date for v in completed)
        stats += f"\n🕓 Последняя тренировка: {last.strftime('%d.%m.%Y')}"
    lines.append(stats)
    return lines


@inject
async def client_detail_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    client_id: int = dialog_manager.dialog_data["viewing_client_id"]
    trainer_id: int = dialog_manager.start_data["trainer_id"]

    client: Client = await mediator.handle(GetClientByIdRequest(client_id=client_id))

    questions: list[RegistrationQuestion] = await mediator.handle(
        GetAllRegistrationQuestionsRequest(trainer_id=trainer_id)
    )
    answers: list[ClientAnswer] = await mediator.handle(
        GetClientAnswersRequest(client_id=client_id)
    )
    answers_by_question = {a.question_id: a.value for a in answers}
    answers_lines = [
        f"• {escape(q.label)}: {escape(', '.join(answers_by_question[q.id]))}"
        for q in questions
        if answers_by_question.get(q.id)
    ]

    recurring_list: list[RecurringBooking] = await mediator.handle(
        GetActiveRecurringBookingsByTrainerRequest(trainer_id=trainer_id)
    )
    client_recurring = sorted(
        (r for r in recurring_list if r.client_id == client_id),
        key=lambda r: (r.weekday, r.start_time),
    )

    lines = [f"👤 <b>{escape(client.full_name)}</b>", _contacts(client)]
    profile = []
    if client.age:
        profile.append(f"🎂 {client.age} лет")
    if client.sport_experience:
        profile.append(f"🏋️ Стаж: {SPORT_EXPERIENCE_LABELS.get(client.sport_experience, '—')}")
    if profile:
        lines.append(" · ".join(profile))
    if client.trainer_note:
        lines.append(f"📝 <i>{escape(client.trainer_note)}</i>")
    if client_recurring:
        lines.append(
            "🔁 Постоянно: "
            + ", ".join(
                f"{WEEKDAY_SHORT[r.weekday]} {r.start_time.strftime('%H:%M')}"
                for r in client_recurring
            )
        )
    lines.append("")
    lines.extend(await _client_card_lines(mediator, trainer_id, client))
    if answers_lines:
        lines.append("\n📋 <b>Анкета:</b>\n" + "\n".join(answers_lines))

    return {
        "card": "\n".join(lines),
        "is_offline": not client.has_telegram,
        "from_outside": dialog_manager.dialog_data.get("from_outside", False),
    }


@inject
async def edit_menu_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    client: Client = await mediator.handle(
        GetClientByIdRequest(client_id=dialog_manager.dialog_data["viewing_client_id"])
    )
    return {
        "full_name": escape(client.full_name),
        # имя/фамилию/телефон клиента из Telegram он заполнил сам — тренер
        # правит только заметку, чтобы не разойтись с анкетой
        "is_offline": not client.has_telegram,
    }


async def edit_value_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    field = ClientEditableField(dialog_manager.dialog_data["editing_field"])
    return {
        "prompt": EDIT_FIELD_PROMPTS[field],
        "can_clear": field != ClientEditableField.FIRST_NAME,
    }


@inject
async def invite_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    client: Client = await mediator.handle(
        GetClientByIdRequest(client_id=dialog_manager.dialog_data["viewing_client_id"])
    )
    link = (
        f"https://t.me/{settings.telegram.bot_username}?start={CLIENT_INVITE_PREFIX}{client.invite_token}"
        if client.invite_token
        else None
    )
    return {"full_name": escape(client.full_name), "link": link or "—", "has_link": link is not None}


@inject
async def book_day_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    # тренеру доступен весь материализованный буфер слотов, а не только
    # горизонт записи клиентов
    availability: dict[date, int] = await mediator.handle(
        GetDayAvailabilityMapRequest(trainer_id=trainer_id, days_ahead=CALENDAR_BUFFER_DAYS)
    )
    dialog_manager.dialog_data[AVAILABILITY_CACHE_KEY] = {
        d.isoformat(): count for d, count in availability.items()
    }
    dialog_manager.dialog_data[HORIZON_CACHE_KEY] = CALENDAR_BUFFER_DAYS
    client: Client = await mediator.handle(
        GetClientByIdRequest(client_id=dialog_manager.dialog_data["viewing_client_id"])
    )
    return {"full_name": escape(client.full_name)}


@inject
async def book_time_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    day = date.fromisoformat(dialog_manager.dialog_data["book_day"])
    return {
        "times": await free_slot_options(mediator, trainer_id, day),
        "day_label": short_day(day),
    }


@inject
async def book_confirm_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    slot: CalendarSlot = await mediator.handle(
        GetSlotByIdRequest(slot_id=dialog_manager.dialog_data["book_slot_id"])
    )
    client: Client = await mediator.handle(
        GetClientByIdRequest(client_id=dialog_manager.dialog_data["viewing_client_id"])
    )
    return {
        "full_name": escape(client.full_name),
        "day_label": short_day(slot.slot_date),
        "time": slot.start_time.strftime("%H:%M"),
        "notify_hint": (
            "Клиент получит уведомление и напоминание."
            if client.has_telegram
            else "📵 Клиент без Telegram — предупредите его сами."
        ),
    }
