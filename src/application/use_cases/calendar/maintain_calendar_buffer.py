import logging
from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.repositories.trainer import TrainerRepository
from src.domain.services.calendar_service import CalendarService
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class MaintainCalendarBufferRequest(UseCaseRequest):
    days_ahead: int = 60 


@dataclass(kw_only=True)
class MaintainCalendarBufferUseCase(UseCase[MaintainCalendarBufferRequest, None]):
    calendar_service: CalendarService
    trainer_repo: TrainerRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: MaintainCalendarBufferRequest) -> None:
        logger.info("[MaintainCalendarBuffer] days_ahead=%s", command.days_ahead)

        # MVP: один активный тренер. При партнёрской модели здесь будет
        # get_all_active() и цикл по каждому, без изменения остальной логики.
        trainer = await self.trainer_repo.get_default_active()
        if trainer is None:
            logger.info("[MaintainCalendarBuffer:skip] no active trainer found")
            return

        new_slots = await self.calendar_service.generate_slots_for_period(
            trainer_id=trainer.id,
            days_ahead=command.days_ahead,
        )
        await self.transaction_manager.commit()

        logger.info(
            "[MaintainCalendarBuffer:done] trainer_id=%s created=%s",
            trainer.id,
            len(new_slots),
        )