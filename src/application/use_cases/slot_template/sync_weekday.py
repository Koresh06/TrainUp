import logging
from dataclasses import dataclass
from datetime import date, time, timedelta

from src.domain.constants import (
    DEFAULT_CALENDAR_HORIZON_DAYS,
    SLOT_DURATION_MINUTES,
    add_minutes,
)
from src.domain.entities.slot_template import SlotTemplate
from src.domain.entities.trainer_booking_settings import TrainerBookingSettings
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.slot_template import SlotTemplateRepository
from src.domain.repositories.trainer_booking_settings import TrainerBookingSettingsRepository
from src.domain.services.calendar_service import CalendarService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class SyncWeekdaySlotTemplatesRequest(UseCaseRequest):
    trainer_id: int
    weekday: int
    selected_times: list[time]
    capacity: int

@dataclass(kw_only=True)
class SyncWeekdaySlotTemplatesUseCase(UseCase[SyncWeekdaySlotTemplatesRequest, None]):
    template_repo: SlotTemplateRepository
    slot_repo: CalendarSlotRepository
    calendar_service: CalendarService
    booking_settings_repo: TrainerBookingSettingsRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: SyncWeekdaySlotTemplatesRequest) -> None:
        existing = await self.template_repo.get_by_trainer_and_weekday(
            command.trainer_id, command.weekday
        )
        existing_by_time = {t.start_time: t for t in existing}
        selected = set(command.selected_times)

        for start_time in selected:
            template = existing_by_time.get(start_time)
            if template is not None:
                template.is_active = True
                template.capacity = command.capacity
                await self.template_repo.save(template)
            else:
                new_template = SlotTemplate(
                    trainer_id=command.trainer_id,
                    weekday=command.weekday,
                    start_time=start_time,
                    end_time=add_minutes(start_time, SLOT_DURATION_MINUTES),
                    capacity=command.capacity,
                    is_active=True,
                )
                await self.template_repo.save(new_template)

        deactivated_times: list[time] = []
        for start_time, template in existing_by_time.items():
            if template.is_active and start_time not in selected:
                template.is_active = False
                await self.template_repo.save(template)
                deactivated_times.append(start_time)

        await self.transaction_manager.commit()

        settings: TrainerBookingSettings | None = (
            await self.booking_settings_repo.get_by_trainer_id(command.trainer_id)
        )
        horizon_days = (
            settings.calendar_horizon_days
            if settings is not None
            else DEFAULT_CALENDAR_HORIZON_DAYS
        )

        new_slots = await self.calendar_service.generate_slots_for_period(
            command.trainer_id, days_ahead=horizon_days
        )
        await self.transaction_manager.commit()
        logger.info("[SyncWeekdaySlotTemplates] new_slots created: %s", len(new_slots))

        # === НОВЫЙ БЛОК — синхронизация capacity на уже существующих слотах ===
        today = date.today()
        all_future_slots = await self.slot_repo.get_slots_for_range(
            command.trainer_id, today, today + timedelta(days=horizon_days)
        )
        updated_count = 0
        for slot in all_future_slots:
            if slot.slot_date.weekday() != command.weekday:
                continue
            if slot.start_time in selected and slot.capacity != command.capacity:
                slot.capacity = command.capacity
                await self.slot_repo.save(slot)
                updated_count += 1

        await self.transaction_manager.commit()
        logger.info("[SyncWeekdaySlotTemplates] capacity synced on %s slots", updated_count)
        # === КОНЕЦ НОВОГО БЛОКА ===

        if deactivated_times:
            free_slots = await self.slot_repo.get_free_slots(
                command.trainer_id,
                today,
                today + timedelta(days=horizon_days),
            )
            for slot in free_slots:
                if slot.start_time in deactivated_times:
                    slot.block()
                    await self.slot_repo.save(slot)
            await self.transaction_manager.commit()

        logger.info(
            "[SyncWeekdaySlotTemplates:done] trainer_id=%s weekday=%s capacity=%s",
            command.trainer_id,
            command.weekday,
            command.capacity,
        )