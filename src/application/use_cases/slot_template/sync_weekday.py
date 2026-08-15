import logging
from dataclasses import dataclass
from datetime import date, time, timedelta

from src.domain.constants import SLOT_DURATION_MINUTES, add_minutes
from src.domain.entities.slot_template import SlotTemplate
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.slot_template import SlotTemplateRepository
from src.domain.services.calendar_service import CalendarService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.infrastructure.database.transaction_manager.base import TransactionManager


logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class SyncWeekdaySlotTemplatesRequest(UseCaseRequest):
    trainer_id: int
    weekday: int
    selected_times: list[time]


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
        selected = set(command.selected_times)

        # активируем выбранные: реактивируем существующие или создаём новые
        for start_time in selected:
            template = existing_by_time.get(start_time)
            if template is not None:
                if not template.is_active:
                    template.is_active = True
                    await self.template_repo.save(template)
            else:
                new_template = SlotTemplate(
                    trainer_id=command.trainer_id,
                    weekday=command.weekday,
                    start_time=start_time,
                    end_time=add_minutes(start_time, SLOT_DURATION_MINUTES),
                    is_active=True,
                )
                await self.template_repo.save(new_template)

        # деактивируем то, что было активно, но сейчас не выбрано
        deactivated_times: list[time] = []
        for start_time, template in existing_by_time.items():
            if template.is_active and start_time not in selected:
                template.is_active = False
                await self.template_repo.save(template)
                deactivated_times.append(start_time)

        await self.transaction_manager.commit()

        templates_check = await self.template_repo.get_active_by_trainer(command.trainer_id)
        logger.info("[DEBUG] active templates after commit: %s", len(templates_check))

        new_slots = await self.calendar_service.generate_slots_for_period(
            command.trainer_id, days_ahead=60
        )
        await self.transaction_manager.commit()
        logger.info("[DEBUG] new_slots created: %s", len(new_slots))

        # освобождаем уже сгенерированные, но ещё не забронированные слоты
        # по деактивированным временам (правило, которое обсуждали в самом начале)
        if deactivated_times:
            free_slots = await self.slot_repo.get_free_slots(
                command.trainer_id,
                date.today(),
                date.today() + timedelta(days=60),
            )
            for slot in free_slots:
                if slot.start_time in deactivated_times:
                    slot.block()
                    await self.slot_repo.save(slot)
            await self.transaction_manager.commit()

        logger.info(
            "[SyncWeekdaySlotTemplates:done] trainer_id=%s weekday=%s",
            command.trainer_id,
            command.weekday,
        )
