from datetime import date

from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.slot_template import SlotTemplate
from src.domain.enums.slot import SlotStatus


class FakeCalendarSlotRepository:
    """In-memory fake implementing CalendarSlotRepository for tests."""

    def __init__(self) -> None:
        self._slots: dict[int, CalendarSlot] = {}
        self._next_id = 1
        self.save_many_call_count = 0

    async def get_by_id(self, slot_id: int) -> CalendarSlot | None:
        return self._slots.get(slot_id)

    async def get_free_slots(
        self,
        trainer_id: int,
        date_from: date,
        date_to: date,
    ) -> list[CalendarSlot]:
        result = [
            slot
            for slot in self._slots.values()
            if slot.trainer_id == trainer_id
            and slot.status == SlotStatus.FREE
            and date_from <= slot.slot_date <= date_to
        ]
        result.sort(key=lambda slot: (slot.slot_date, slot.start_time))
        return result

    async def exists_for_date(self, trainer_id: int, date: date) -> bool:
        return any(
            slot.trainer_id == trainer_id and slot.slot_date == date
            for slot in self._slots.values()
        )

    async def save(self, slot: CalendarSlot) -> CalendarSlot:
        if slot.id == 0:
            slot.id = self._next_id
            self._next_id += 1
        self._slots[slot.id] = slot
        return slot

    async def save_many(self, slots: list[CalendarSlot]) -> list[CalendarSlot]:
        self.save_many_call_count += 1
        for slot in slots:
            await self.save(slot)
        return slots


class FakeSlotTemplateRepository:
    """In-memory fake implementing SlotTemplateRepository for tests."""

    def __init__(self, templates: list[SlotTemplate] | None = None) -> None:
        self._templates: list[SlotTemplate] = list(templates) if templates else []
        self._next_id = 1

    async def get_active_by_trainer(self, trainer_id: int) -> list[SlotTemplate]:
        return [
            template
            for template in self._templates
            if template.trainer_id == trainer_id and template.is_active
        ]

    async def save(self, slot_template: SlotTemplate) -> SlotTemplate:
        if slot_template.id == 0:
            slot_template.id = self._next_id
            self._next_id += 1
            self._templates.append(slot_template)
        return slot_template

    async def delete(self, slot_template: SlotTemplate) -> None:
        self._templates = [t for t in self._templates if t.id != slot_template.id]
