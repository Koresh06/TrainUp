from dataclasses import dataclass
from datetime import date, timedelta

from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.slot_template import SlotTemplate
from src.domain.enums.slot import SlotSource, SlotStatus
from src.domain.exception.booking import SlotAlreadyBookedException
from src.domain.exception.calendar_slot import CalendarSlotNotFoundException
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.slot_template import SlotTemplateRepository


@dataclass
class CalendarService:
    slot_repo: CalendarSlotRepository
    template_repo: SlotTemplateRepository

    async def generate_slots_for_period(
        self,
        trainer_id: int,
        days_ahead: int,
    ) -> list[CalendarSlot]:
        templates = await self.template_repo.get_active_by_trainer(trainer_id)
        if not templates:
            return []

        template_by_wekday: dict[int, list[SlotTemplate]] = {}
        for template in templates:
            template_by_wekday.setdefault(template.weekday, []).append(template)

        today = date.today()
        new_slots: list[CalendarSlot] = []

        for offset in range(days_ahead + 1):
            current_date = today + timedelta(days=offset)

            if await self.slot_repo.exists_for_date(trainer_id, current_date):
                continue

            weekday = current_date.weekday()
            for template in template_by_wekday.get(weekday, []):
                new_slots.append(
                    CalendarSlot(
                        trainer_id=trainer_id,
                        slot_date=current_date,
                        start_time=template.start_time,
                        end_time=template.end_time,
                        status=SlotStatus.FREE,
                        source=SlotSource.TEMPLATE,
                    )
                )

        if new_slots:
            await self.slot_repo.save_many(new_slots)

        return new_slots

    async def get_free_slots(self, trainer_id: int, days_ahead: int) -> list[CalendarSlot]:
        today = date.today()
        date_to = today + timedelta(days=days_ahead)
        return await self.slot_repo.get_free_slots(trainer_id, today, date_to)

    async def book_slot(self, slot_id: int) -> CalendarSlot:
        slot = await self.slot_repo.get_by_id(slot_id)
        if slot is None:
            raise CalendarSlotNotFoundException(slot_id)

        if not slot.is_available():
            raise SlotAlreadyBookedException(slot_id)

        slot.book()
        return await self.slot_repo.save(slot)

    async def release_slot(self, slot_id: int) -> CalendarSlot:
        slot = await self.slot_repo.get_by_id(slot_id)
        if slot is None:
            raise CalendarSlotNotFoundException(slot_id)

        slot.release()
        return await self.slot_repo.save(slot)

    async def block_slot(self, slot_id: int) -> CalendarSlot:
        slot = await self.slot_repo.get_by_id(slot_id)
        if slot is None:
            raise CalendarSlotNotFoundException(slot_id)

        slot.block()
        return await self.slot_repo.save(slot)

    async def get_slots_for_date(self, trainer_id: int, slot_date: date) -> list[CalendarSlot]:
        return await self.slot_repo.get_slots_for_date(trainer_id, slot_date)

    async def get_week_grid_slots(self, trainer_id: int, days_ahead: int) -> list[CalendarSlot]:
        today = date.today()
        date_to = today + timedelta(days=days_ahead)
        return await self.slot_repo.get_slots_for_range(trainer_id, today, date_to)