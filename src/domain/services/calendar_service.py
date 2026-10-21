from dataclasses import dataclass
from datetime import date, timedelta

from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.slot_template import SlotTemplate
from src.domain.enums.slot import SlotSource, SlotStatus
from src.domain.exception.booking import SlotAlreadyBookedException
from src.domain.exception.calendar_slot import (
    CalendarSlotNotFoundException,
    SlotFullException,
    SlotInPastException,
)
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.slot_template import SlotTemplateRepository
from src.domain.repositories.trainer_vacation import TrainerVacationRepository
from src.domain.utils import get_project_today, is_slot_in_past


@dataclass
class CalendarService:
    slot_repo: CalendarSlotRepository
    template_repo: SlotTemplateRepository
    booking_repo: BookingRepository
    # отпуск тренера: слоты, сгенерированные внутри периода, сразу закрыты
    vacation_repo: TrainerVacationRepository | None = None

    async def generate_slots_for_period(
        self, trainer_id: int, days_ahead: int
    ) -> list[CalendarSlot]:
        templates = await self.template_repo.get_active_by_trainer(trainer_id)
        if not templates:
            return []

        template_by_weekday: dict[int, list[SlotTemplate]] = {}
        for template in templates:
            template_by_weekday.setdefault(template.weekday, []).append(template)

        today = get_project_today()
        new_slots: list[CalendarSlot] = []
        vacations = (
            await self.vacation_repo.get_by_trainer(trainer_id, today)
            if self.vacation_repo is not None
            else []
        )

        for offset in range(days_ahead + 1):
            current_date = today + timedelta(days=offset)
            weekday = current_date.weekday()

            for template in template_by_weekday.get(weekday, []):
                exists = await self.slot_repo.exists_for_datetime(
                    trainer_id, current_date, template.start_time
                )
                if exists:
                    continue
                new_slots.append(
                    CalendarSlot(
                        trainer_id=trainer_id,
                        slot_date=current_date,
                        start_time=template.start_time,
                        end_time=template.end_time,
                        status=(
                            SlotStatus.BLOCKED
                            if any(v.covers(current_date) for v in vacations)
                            else SlotStatus.FREE
                        ),
                        source=SlotSource.TEMPLATE,
                        capacity=template.capacity,
                    )
                )

        if new_slots:
            await self.slot_repo.save_many(new_slots)
        return new_slots

    async def get_free_slots(
        self, trainer_id: int, days_ahead: int
    ) -> list[CalendarSlot]:
        today = get_project_today()
        date_to = today + timedelta(days=days_ahead)
        return await self.slot_repo.get_free_slots(trainer_id, today, date_to)

    async def book_slot(self, slot_id: int) -> CalendarSlot:
        slot = await self.slot_repo.get_by_id_for_update(slot_id)
        if slot is None:
            raise CalendarSlotNotFoundException(slot_id)
    
        self._ensure_bookable(slot)
    
        active_count = await self.booking_repo.count_active_by_slot_id(slot_id)
        if active_count >= slot.capacity:
            raise SlotFullException(slot_id)
    
        # status больше не переключаем в BOOKED — capacity важнее бинарного статуса;
        # BOOKED теперь смысловое значение теряет для capacity>1, оставляем FREE
        # если ещё есть места, либо явно помечаем занятым только когда мест не осталось
        if active_count + 1 >= slot.capacity:
            slot.status = SlotStatus.BOOKED
            slot.touch()
            await self.slot_repo.save(slot)
    
        return slot

    async def release_slot(self, slot_id: int) -> CalendarSlot:
        slot = await self.slot_repo.get_by_id(slot_id)
        if slot is None:
            raise CalendarSlotNotFoundException(slot_id)
    
        if slot.status != SlotStatus.BLOCKED:
            slot.release()
            await self.slot_repo.save(slot)
    
        return slot

    async def block_slot(self, slot_id: int) -> CalendarSlot:
        slot = await self.slot_repo.get_by_id(slot_id)
        if slot is None:
            raise CalendarSlotNotFoundException(slot_id)

        slot.block()
        return await self.slot_repo.save(slot)

    async def unblock_slot(self, slot_id: int) -> CalendarSlot:
        """
        Снятие блокировки: статус восстанавливаем по факту занятости —
        если активных записей уже на всю вместимость, слот остаётся BOOKED.
        """
        slot = await self.slot_repo.get_by_id(slot_id)
        if slot is None:
            raise CalendarSlotNotFoundException(slot_id)

        if slot.status != SlotStatus.BLOCKED:
            return slot

        active_count = await self.booking_repo.count_active_by_slot_id(slot_id)
        slot.status = (
            SlotStatus.BOOKED if active_count >= slot.capacity else SlotStatus.FREE
        )
        slot.touch()
        return await self.slot_repo.save(slot)

    async def get_slots_for_date(
        self, trainer_id: int, slot_date: date
    ) -> list[CalendarSlot]:
        # неактивные слоты — времена, убранные тренером из шаблона расписания
        slots = await self.slot_repo.get_slots_for_date(trainer_id, slot_date)
        return [s for s in slots if s.is_active]

    async def get_week_grid_slots(
        self, trainer_id: int, days_ahead: int
    ) -> list[CalendarSlot]:
        today = get_project_today()
        date_to = today + timedelta(days=days_ahead)
        slots = await self.slot_repo.get_slots_for_range(trainer_id, today, date_to)
        return [s for s in slots if s.is_active]

    async def book_slot_forced(self, slot_id: int) -> CalendarSlot:
        """
        Бронирование без проверки capacity — для постоянных клиентов (RecurringBooking),
        у которых есть безусловное право на своё время, даже если слот формально
        переполнен обычными клиентами.
        """
        slot = await self.slot_repo.get_by_id_for_update(slot_id)
        if slot is None:
            raise CalendarSlotNotFoundException(slot_id)
    
        self._ensure_bookable(slot)
    
        active_count = await self.booking_repo.count_active_by_slot_id(slot_id)
        if active_count + 1 >= slot.capacity:
            slot.status = SlotStatus.BOOKED
            slot.touch()
            await self.slot_repo.save(slot)
    
        return slot

    @staticmethod
    def _ensure_bookable(slot: CalendarSlot) -> None:
        if slot.status == SlotStatus.BLOCKED or not slot.is_active:
            raise SlotAlreadyBookedException(slot.id)
        if is_slot_in_past(slot):
            raise SlotInPastException(slot.id)
