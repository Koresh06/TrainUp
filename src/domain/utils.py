from datetime import datetime, timezone

from src.domain.entities.calendar_slot import CalendarSlot


def get_training_datetime_utc(slot: CalendarSlot) -> datetime:
    dt = datetime.combine(slot.slot_date, slot.start_time)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt