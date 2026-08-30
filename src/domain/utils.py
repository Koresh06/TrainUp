from datetime import datetime

from src.domain.entities.calendar_slot import CalendarSlot


def get_training_datetime_utc(slot: CalendarSlot) -> datetime:
    return datetime.combine(slot.slot_date, slot.start_time)