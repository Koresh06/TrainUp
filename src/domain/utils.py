from datetime import datetime, timezone

from src.domain.constants import PROJECT_TIMEZONE
from src.domain.entities.calendar_slot import CalendarSlot


def get_training_datetime_utc(slot: CalendarSlot) -> datetime:
    naive_local = datetime.combine(slot.slot_date, slot.start_time.replace(tzinfo=None))
    aware_local = naive_local.replace(tzinfo=PROJECT_TIMEZONE)
    return aware_local.astimezone(timezone.utc).replace(tzinfo=None)