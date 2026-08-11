from typing import Protocol
from datetime import date

from src.domain.entities.calendar_slot import CalendarSlot


class CalendarSlotRepository(Protocol):
    async def get_by_id(self, slot_id: int) -> CalendarSlot | None: ...

    async def get_free_slots(
        self,
        trainer_id: int,
        date_from: date,
        date_to: date,
    ) -> list[CalendarSlot]: ...

    async def exists_for_date(self, trainer_id: int, date: date) -> bool: ...

    async def save(self, slot: CalendarSlot) -> CalendarSlot: ...

    async def save_many(self, slots: list[CalendarSlot]) -> list[CalendarSlot]: ...

    async def get_slots_for_date(
        self,
        trainer_id: int,
        slot_date: date,
    ) -> list[CalendarSlot]: ...

    async def get_slots_for_range(
        self,
        trainer_id: int,
        date_from: date,
        date_to: date,
    ) -> list[CalendarSlot]: ...
