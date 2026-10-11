from datetime import date, datetime, timezone

from src.domain.constants import PROJECT_TIMEZONE
from src.domain.entities.calendar_slot import CalendarSlot
from src.utils.get_datetime_utc_now import get_datetime_utc_now


def get_training_datetime_utc(slot: CalendarSlot) -> datetime:
    naive_local = datetime.combine(slot.slot_date, slot.start_time.replace(tzinfo=None))
    aware_local = naive_local.replace(tzinfo=PROJECT_TIMEZONE)
    return aware_local.astimezone(timezone.utc).replace(tzinfo=None)


def get_project_today() -> date:
    """Сегодняшняя дата в часовом поясе проекта (а не сервера) — в Docker
    сервер живёт в UTC, и date.today() с 21:00 до 00:00 по Москве отдаёт
    уже вчерашний день."""
    return datetime.now(PROJECT_TIMEZONE).date()


def is_slot_in_past(slot: CalendarSlot) -> bool:
    """Слот уже начался/прошёл — записываться/переносить на него нельзя."""
    return get_training_datetime_utc(slot) <= get_datetime_utc_now()
