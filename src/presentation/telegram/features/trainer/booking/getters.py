from datetime import date, timedelta
from decimal import Decimal
from html import escape

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.booking.get_by_id import GetBookingByIdRequest
from src.application.use_cases.booking.get_views import GetBookingViewsRequest
from src.application.use_cases.calendar.get_day_availability_map import (
    GetDayAvailabilityMapRequest,
)
from src.application.use_cases.calendar.get_slot_by_id import GetSlotByIdRequest
from src.application.use_cases.client.get_by_id import GetClientByIdRequest
from src.application.use_cases.client.get_clients_by_trainer import (
    GetClientsByTrainerIdRequest,
)
from src.domain.constants import CALENDAR_BUFFER_DAYS
from src.domain.entities.booking import Booking
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.client import Client
from src.domain.enums.booking import (
    ACTIVE_BOOKING_STATUSES,
    BookingActor,
    BookingStatus,
    HistoryFilter,
    PAST_BOOKING_STATUSES,
)
from src.domain.repositories.booking import BookingView
from src.domain.utils import get_project_today, get_training_datetime_utc
from src.presentation.telegram.charts.text import byn
from src.presentation.telegram.common.booking_labels import (
    MONTHS_NOMINATIVE,
    STATUS_ICONS,
    STATUS_TITLES,
    WEEKDAY_SHORT,
    booking_badges,
    day_title,
    short_day,
)
from src.presentation.telegram.common.free_slots import free_slot_options
from src.presentation.telegram.widgets.booking_calendar import (
    AVAILABILITY_CACHE_KEY,
    BUSY_DAYS_CACHE_KEY,
    HORIZON_CACHE_KEY,
    SCHEDULE_PAST_DAYS,
)
from src.utils.get_datetime_utc_now import get_datetime_utc_now
from src.utils.timezone import to_moscow

DAY_KEY = "day"
WEEK_KEY = "week_start"
MONTH_KEY = "history_month"
FILTER_KEY = "history_filter"
BOOKING_KEY = "booking_id"

HISTORY_FILTER_LABELS: dict[HistoryFilter, str] = {
    HistoryFilter.ALL: "Все",
    HistoryFilter.COMPLETED: "🏁 Проведены",
    HistoryFilter.CANCELLED: "❌ Отмены",
    HistoryFilter.NO_SHOW: "🚫 Неявки",
}
HISTORY_STATUSES: dict[HistoryFilter, tuple[BookingStatus, ...]] = {
    HistoryFilter.ALL: (*PAST_BOOKING_STATUSES, BookingStatus.CANCELLED),
    HistoryFilter.COMPLETED: (BookingStatus.COMPLETED,),
    HistoryFilter.CANCELLED: (BookingStatus.CANCELLED,),
    HistoryFilter.NO_SHOW: (BookingStatus.NO_SHOW,),
}
CANCELLED_BY_LABELS: dict[BookingActor, str] = {
    BookingActor.TRAINER: "вы",
    BookingActor.CLIENT: "клиент",
    BookingActor.SYSTEM: "автоматически",
}


def current_day(dialog_manager: DialogManager) -> date:
    raw = dialog_manager.dialog_data.get(DAY_KEY)
    return date.fromisoformat(raw) if raw else get_project_today()


def trainings_word(n: int) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return "тренировка"
    if 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return "тренировки"
    return "тренировок"


def _line(view: BookingView) -> str:
    """Строка расписания дня: «<code>09:00</code> ✅ Иван Петров 🔁»."""
    status = view.booking.status
    line = (
        f"<code>{view.start_time.strftime('%H:%M')}</code> {STATUS_ICONS.get(status, '')} "
        f"{escape(view.client_full_name)}{booking_badges(view)}"
    )
    if status == BookingStatus.PENDING:
        line += " — <i>ждёт подтверждения</i>"
    return line


def _button(view: BookingView, with_day: bool = False) -> dict:
    prefix = f"{short_day(view.slot_date)} " if with_day else ""
    return {
        "id": str(view.booking.id),
        "label": (
            f"{prefix}{view.start_time.strftime('%H:%M')} "
            f"{STATUS_ICONS.get(view.booking.status, '')} {view.client_short_name}"
            f"{booking_badges(view)}"
        ),
    }


def _money_line(views: list[BookingView]) -> str:
    total = sum(
        (v.booking.price for v in views if v.booking.price and v.booking.status != BookingStatus.NO_SHOW),
        Decimal("0"),
    )
    return f" · ≈ {byn(total)}" if total else ""


async def _pending(mediator: Mediator, trainer_id: int) -> list[BookingView]:
    return await mediator.handle(
        GetBookingViewsRequest(
            trainer_id=trainer_id,
            date_from=get_project_today(),
            statuses=(BookingStatus.PENDING,),
        )
    )


@inject
async def day_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    day = current_day(dialog_manager)
    today = get_project_today()

    views: list[BookingView] = await mediator.handle(
        GetBookingViewsRequest(trainer_id=trainer_id, date_from=day, date_to=day)
    )
    shown = [v for v in views if v.booking.status != BookingStatus.CANCELLED]
    cancelled = len(views) - len(shown)

    if shown:
        summary = f"{len(shown)} {trainings_word(len(shown))}{_money_line(shown)}"
        body = "\n".join(_line(v) for v in shown)
    else:
        summary = "Записей нет" + (" — свободный день 🙌" if day >= today else "")
        body = ""
    if cancelled:
        summary += f"\n<i>отменено: {cancelled}</i>"

    pending = await _pending(mediator, trainer_id)
    return {
        "title": day_title(day),
        "summary": summary,
        "body": f"\n\n{body}" if body else "",
        "bookings": [_button(v) for v in shown],
        "prev_label": f"◀️ {short_day(day - timedelta(days=1))}",
        "next_label": f"{short_day(day + timedelta(days=1))} ▶️",
        "not_today": day != today,
        "can_add": day >= today,
        "pending_count": len(pending),
        "has_pending": bool(pending),
    }


@inject
async def week_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    raw = dialog_manager.dialog_data.get(WEEK_KEY)
    start = date.fromisoformat(raw) if raw else current_day(dialog_manager)
    start -= timedelta(days=start.weekday())
    end = start + timedelta(days=6)

    views: list[BookingView] = await mediator.handle(
        GetBookingViewsRequest(trainer_id=trainer_id, date_from=start, date_to=end)
    )
    shown = [v for v in views if v.booking.status != BookingStatus.CANCELLED]
    by_day: dict[date, list[BookingView]] = {}
    for v in shown:
        by_day.setdefault(v.slot_date, []).append(v)

    blocks = []
    days = []
    for offset in range(7):
        d = start + timedelta(days=offset)
        items = by_day.get(d, [])
        header = f"<b>{short_day(d)}</b>" + (" · сегодня" if d == get_project_today() else "")
        if items:
            lines = "\n".join(_line(v) for v in items)
            blocks.append(f"\n{header}\n{lines}\n")
        else:
            # свободные дни — одной строкой подряд, чтобы неделя помещалась на экран
            blocks.append(f"{header} — свободно")
        days.append(
            {"id": d.isoformat(), "label": f"{WEEKDAY_SHORT[d.weekday()]} {d.day}" + (f" ({len(items)})" if items else "")}
        )

    return {
        "title": f"{start.strftime('%d.%m')} – {end.strftime('%d.%m')}",
        "summary": f"{len(shown)} {trainings_word(len(shown))}{_money_line(shown)}",
        "body": "\n".join(blocks).strip().replace("\n\n\n", "\n\n"),
        "days": days,
    }


@inject
async def pick_date_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    today = get_project_today()
    views: list[BookingView] = await mediator.handle(
        GetBookingViewsRequest(
            trainer_id=trainer_id,
            date_from=today - timedelta(days=SCHEDULE_PAST_DAYS),
            date_to=today + timedelta(days=CALENDAR_BUFFER_DAYS),
            statuses=(*ACTIVE_BOOKING_STATUSES, *PAST_BOOKING_STATUSES),
        )
    )
    busy: dict[str, int] = {}
    for v in views:
        busy[v.slot_date.isoformat()] = busy.get(v.slot_date.isoformat(), 0) + 1
    dialog_manager.dialog_data[BUSY_DAYS_CACHE_KEY] = busy
    dialog_manager.dialog_data[HORIZON_CACHE_KEY] = CALENDAR_BUFFER_DAYS
    return {}


@inject
async def pending_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    views = await _pending(mediator, trainer_id)
    return {
        "bookings": [_button(v, with_day=True) for v in views],
        "empty_hint": "" if views else "\n\nНовых записей нет 👌",
    }


def _month_bounds(raw: str | None) -> tuple[date, date]:
    today = get_project_today()
    first = date.fromisoformat(f"{raw}-01") if raw else today.replace(day=1)
    next_month = (first + timedelta(days=32)).replace(day=1)
    return first, next_month - timedelta(days=1)


def shift_month(raw: str | None, delta: int) -> str:
    first, _ = _month_bounds(raw)
    if delta < 0:
        target = (first - timedelta(days=1)).replace(day=1)
    else:
        target = (first + timedelta(days=32)).replace(day=1)
    return target.strftime("%Y-%m")


@inject
async def history_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    today = get_project_today()
    raw_month = dialog_manager.dialog_data.get(MONTH_KEY)
    first, last = _month_bounds(raw_month)
    current_filter = HistoryFilter(dialog_manager.dialog_data.get(FILTER_KEY, HistoryFilter.ALL.value))

    views: list[BookingView] = await mediator.handle(
        GetBookingViewsRequest(
            trainer_id=trainer_id,
            date_from=first,
            date_to=min(last, today),
            statuses=HISTORY_STATUSES[HistoryFilter.ALL],
            newest_first=True,
        )
    )
    counts = {
        status: sum(1 for v in views if v.booking.status == status)
        for status in HISTORY_STATUSES[HistoryFilter.ALL]
    }
    shown = [v for v in views if v.booking.status in HISTORY_STATUSES[current_filter]]
    income = sum(
        (v.booking.price for v in views if v.booking.status == BookingStatus.COMPLETED and v.booking.price),
        Decimal("0"),
    )

    stats = (
        f"🏁 {counts[BookingStatus.COMPLETED]} · ❌ {counts[BookingStatus.CANCELLED]} · "
        f"🚫 {counts[BookingStatus.NO_SHOW]}"
    )
    if income:
        stats += f" · 💰 {byn(income)}"

    prev_first = (first - timedelta(days=1)).replace(day=1)
    next_first = last + timedelta(days=1)
    return {
        "title": f"{MONTHS_NOMINATIVE[first.month - 1]} {first.year}",
        "stats": stats,
        "empty_hint": "" if shown else "\n\nЗа этот месяц записей нет.",
        "bookings": [_button(v, with_day=True) for v in shown],
        "filters": [
            {
                "id": f.value,
                "label": f"• {label} •" if f == current_filter else label,
            }
            for f, label in HISTORY_FILTER_LABELS.items()
        ],
        "prev_label": f"◀️ {MONTHS_NOMINATIVE[prev_first.month - 1]}",
        "next_label": f"{MONTHS_NOMINATIVE[next_first.month - 1]} ▶️",
        "has_next": next_first <= today,
    }


@inject
async def booking_detail_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    booking: Booking = await mediator.handle(
        GetBookingByIdRequest(booking_id=dialog_manager.dialog_data[BOOKING_KEY])
    )
    slot: CalendarSlot = await mediator.handle(GetSlotByIdRequest(slot_id=booking.slot_id))
    client: Client = await mediator.handle(GetClientByIdRequest(client_id=booking.client_id))

    started = get_training_datetime_utc(slot) <= get_datetime_utc_now()
    status = booking.status

    lines = [f"👤 <b>{escape(client.full_name)}</b>"]
    if client.has_telegram:
        contact = f'💬 <a href="tg://user?id={client.tg_id}">Написать</a>'
        if client.username:
            contact += f" · @{escape(client.username)}"
        lines.append(contact)
    else:
        lines.append("📵 Без Telegram — уведомления не получает")
    if client.phone:
        lines.append(f"📞 {escape(client.phone)}")
    if client.trainer_note:
        lines.append(f"📝 <i>{escape(client.trainer_note)}</i>")

    lines.append("")
    lines.append(f"📅 {day_title(slot.slot_date)}")
    lines.append(f"🕐 {slot.start_time.strftime('%H:%M')}–{slot.end_time.strftime('%H:%M')}")
    if booking.price:
        lines.append(f"💰 {byn(booking.price)}")
    lines.append(f"📌 {STATUS_TITLES.get(status, status.value)}")
    if booking.recurring_booking_id is not None:
        lines.append("🔁 Постоянная тренировка")
    if booking.package_id is not None:
        lines.append("🎫 Списано с абонемента")
    elif booking.price and status in PAST_BOOKING_STATUSES:
        lines.append(
            f"💵 Оплачено {to_moscow(booking.paid_at).strftime('%d.%m')}"
            if booking.paid_at
            else "💵 Не оплачено"
        )
    if status == BookingStatus.CANCELLED and booking.cancelled_by is not None:
        when = (
            f" · {to_moscow(booking.cancelled_at).strftime('%d.%m %H:%M')}"
            if booking.cancelled_at
            else ""
        )
        lines.append(f"↪️ Отменил: {CANCELLED_BY_LABELS[booking.cancelled_by]}{when}")

    is_active = status in ACTIVE_BOOKING_STATUSES
    return {
        "card": "\n".join(lines),
        "is_pending": status == BookingStatus.PENDING,
        "can_change": is_active and not started,
        "can_no_show": started and status in (BookingStatus.CONFIRMED, BookingStatus.COMPLETED),
        "can_attended": status == BookingStatus.NO_SHOW,
        "can_mark_paid": (
            status in PAST_BOOKING_STATUSES
            and booking.package_id is None
            and bool(booking.price)
            and booking.paid_at is None
        ),
    }


@inject
async def cancel_confirm_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    booking: Booking = await mediator.handle(
        GetBookingByIdRequest(booking_id=dialog_manager.dialog_data[BOOKING_KEY])
    )
    slot: CalendarSlot = await mediator.handle(GetSlotByIdRequest(slot_id=booking.slot_id))
    client: Client = await mediator.handle(GetClientByIdRequest(client_id=booking.client_id))
    return {
        "client_name": escape(client.full_name),
        "when": f"{short_day(slot.slot_date)} в {slot.start_time.strftime('%H:%M')}",
        "notify_hint": (
            "Клиент получит уведомление об отмене."
            if client.has_telegram
            else "📵 Клиент без Telegram — предупредите его сами."
        ),
        "recurring_hint": (
            "\n🔁 Отменится только эта дата — постоянная запись останется."
            if booking.recurring_booking_id is not None
            else ""
        ),
    }


async def _fill_calendar_cache(dialog_manager: DialogManager, mediator: Mediator) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    # тренеру доступен весь материализованный буфер слотов, а не только горизонт клиентов
    availability: dict[date, int] = await mediator.handle(
        GetDayAvailabilityMapRequest(trainer_id=trainer_id, days_ahead=CALENDAR_BUFFER_DAYS)
    )
    dialog_manager.dialog_data[AVAILABILITY_CACHE_KEY] = {
        d.isoformat(): count for d, count in availability.items()
    }
    dialog_manager.dialog_data[HORIZON_CACHE_KEY] = CALENDAR_BUFFER_DAYS


@inject
async def reschedule_day_calendar_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    await _fill_calendar_cache(dialog_manager, mediator)
    return {}


@inject
async def reschedule_times_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    selected_day = date.fromisoformat(dialog_manager.dialog_data["reschedule_day"])
    return {
        "times": await free_slot_options(mediator, trainer_id, selected_day),
        "selected_day_label": short_day(selected_day),
    }


@inject
async def reschedule_confirm_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    slot: CalendarSlot = await mediator.handle(
        GetSlotByIdRequest(slot_id=dialog_manager.dialog_data["new_slot_id"])
    )
    return {
        "date": short_day(slot.slot_date),
        "time": slot.start_time.strftime("%H:%M"),
    }


@inject
async def add_client_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    clients: list[Client] = await mediator.handle(
        GetClientsByTrainerIdRequest(trainer_id=trainer_id)
    )
    return {
        "day_label": short_day(current_day(dialog_manager)),
        "clients": [
            {"id": str(c.id), "label": ("📵 " if not c.has_telegram else "") + c.full_name}
            for c in clients
            if c.is_active
        ],
        "empty_hint": (
            ""
            if clients
            else "\n\nКлиентов пока нет — добавьте их в «👥 Мои клиенты»."
        ),
    }


@inject
async def add_time_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    day = current_day(dialog_manager)
    times = await free_slot_options(mediator, trainer_id, day)
    return {
        "times": times,
        "day_label": short_day(day),
        "empty_hint": (
            ""
            if times
            else "\n\nСвободного времени нет — добавьте слоты в «⚙️ Настройки → Расписание»."
        ),
    }


@inject
async def add_confirm_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    slot: CalendarSlot = await mediator.handle(
        GetSlotByIdRequest(slot_id=dialog_manager.dialog_data["add_slot_id"])
    )
    client: Client = await mediator.handle(
        GetClientByIdRequest(client_id=dialog_manager.dialog_data["add_client_id"])
    )
    return {
        "client_name": escape(client.full_name),
        "when": f"{short_day(slot.slot_date)} в {slot.start_time.strftime('%H:%M')}",
        "notify_hint": (
            "Клиент получит уведомление и напоминание."
            if client.has_telegram
            else "📵 Клиент без Telegram — предупредите его сами."
        ),
    }
