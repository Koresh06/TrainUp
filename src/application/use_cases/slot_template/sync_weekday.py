import logging
from dataclasses import dataclass
from datetime import time, timedelta

from src.domain.constants import (
    CALENDAR_BUFFER_DAYS,
    SLOT_DURATION_MINUTES,
    add_minutes,
)
from src.domain.entities.slot_template import SlotTemplate
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.slot_template import SlotTemplateRepository
from src.domain.services.calendar_service import CalendarService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.utils import get_project_today
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class SyncWeekdaySlotTemplatesRequest(UseCaseRequest):
    trainer_id: int
    weekday: int
    time_capacities: dict[time, int]


@dataclass(kw_only=True)
class SyncWeekdaySlotTemplatesUseCase(UseCase[SyncWeekdaySlotTemplatesRequest, None]):
    template_repo: SlotTemplateRepository
    slot_repo: CalendarSlotRepository
    calendar_service: CalendarService
    transaction_manager: TransactionManager

    async def __call__(self, command: SyncWeekdaySlotTemplatesRequest) -> None:
        existing = await self.template_repo.get_by_trainer_and_weekday(
            command.trainer_id, command.weekday
        )
        existing_by_time = {t.start_time: t for t in existing}
        selected = command.time_capacities  # {start_time: capacity}, все capacity > 0

        for start_time, capacity in selected.items():
            template = existing_by_time.get(start_time)
            if template is not None:
                template.is_active = True
                template.capacity = capacity
                await self.template_repo.save(template)
            else:
                new_template = SlotTemplate(
                    trainer_id=command.trainer_id,
                    weekday=command.weekday,
                    start_time=start_time,
                    end_time=add_minutes(start_time, SLOT_DURATION_MINUTES),
                    capacity=capacity,
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

        # слоты материализуются на весь буфер (CALENDAR_BUFFER_DAYS), а не только
        # на горизонт клиента — иначе при увеличении горизонта всплывут слоты со
        # старой вместимостью/убранным временем
        new_slots = await self.calendar_service.generate_slots_for_period(
            command.trainer_id, days_ahead=CALENDAR_BUFFER_DAYS
        )
        await self.transaction_manager.commit()
        logger.info("[SyncWeekdaySlotTemplates] new_slots created: %s", len(new_slots))

        today = get_project_today()
        all_future_slots = await self.slot_repo.get_slots_for_range(
            command.trainer_id, today, today + timedelta(days=CALENDAR_BUFFER_DAYS)
        )
        updated_count = 0
        for slot in all_future_slots:
            if slot.slot_date.weekday() != command.weekday:
                continue

            new_capacity = selected.get(slot.start_time)
            if new_capacity is not None:
                # время есть в шаблоне: синхронизируем вместимость и возвращаем
                # слот, если раньше это время убирали из расписания
                changed = slot.capacity != new_capacity or not slot.is_active
                slot.capacity = new_capacity
                slot.is_active = True
            else:
                # время убрали из шаблона: слот скрывается у клиентов, но уже
                # существующие записи на нём сохраняются — тренер видит их в
                # «Бронированиях» и сам решает, отменить или перенести.
                # Ручную блокировку (status=BLOCKED) не трогаем.
                changed = slot.is_active
                slot.is_active = False

            if changed:
                slot.touch()
                await self.slot_repo.save(slot)
                updated_count += 1

        await self.transaction_manager.commit()
        logger.info(
            "[SyncWeekdaySlotTemplates] slots synced: %s (deactivated times: %s)",
            updated_count,
            len(deactivated_times),
        )

        logger.info(
            "[SyncWeekdaySlotTemplates:done] trainer_id=%s weekday=%s times=%s",
            command.trainer_id,
            command.weekday,
            len(selected),
        )
