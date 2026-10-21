from datetime import date

from src.application.mediator import Mediator
from src.application.use_cases.booking.count_active_by_slot_ids import (
    CountActiveBookingsBySlotIdsRequest,
)
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsRequest
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.enums.slot import SlotStatus
from src.domain.utils import is_slot_in_past


async def free_slot_options(mediator: Mediator, trainer_id: int, day: date) -> list[dict]:
    """Свободные (не прошедшие, не закрытые, с местами) слоты дня — кнопки выбора
    времени для переноса и записи клиента тренером."""
    slots: list[CalendarSlot] = await mediator.handle(
        GetDaySlotsRequest(trainer_id=trainer_id, slot_date=day)
    )
    slots = sorted((s for s in slots if not is_slot_in_past(s)), key=lambda s: s.start_time)
    booked = await mediator.handle(
        CountActiveBookingsBySlotIdsRequest(slot_ids=[s.id for s in slots])
    )
    options = []
    for slot in slots:
        free_spots = slot.capacity - booked.get(slot.id, 0)
        if slot.status == SlotStatus.BLOCKED or free_spots <= 0:
            continue
        label = slot.start_time.strftime("%H:%M")
        if slot.capacity > 1:
            label += f" ({free_spots})"
        options.append({"value_id": str(slot.id), "label": label})
    return options
