from datetime import date

from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.enums.booking import ACTIVE_BOOKING_STATUSES
from src.domain.repositories.booking import BookingRepository, BookingView
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.utils import get_project_today, is_slot_in_past


async def period_slots_and_bookings(
    *,
    trainer_id: int,
    date_from: date,
    date_to: date,
    slot_repo: CalendarSlotRepository,
    booking_repo: BookingRepository,
) -> tuple[list[CalendarSlot], list[BookingView]]:
    """Будущие слоты и активные записи периода (прошлое не трогаем)."""
    start = max(date_from, get_project_today())
    if start > date_to:
        return [], []
    slots = [
        s for s in await slot_repo.get_slots_for_range(trainer_id, start, date_to)
        if s.is_active and not is_slot_in_past(s)
    ]
    slot_ids = {s.id for s in slots}
    views = [
        v for v in await booking_repo.get_views(
            trainer_id=trainer_id,
            date_from=start,
            date_to=date_to,
            statuses=ACTIVE_BOOKING_STATUSES,
        )
        if v.booking.slot_id in slot_ids
    ]
    return slots, views
