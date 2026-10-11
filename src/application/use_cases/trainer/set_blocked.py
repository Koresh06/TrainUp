import logging
from dataclasses import dataclass

from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.trainer import Trainer
from src.domain.exception.trainer import TrainerNotFoundException
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class SetTrainerBlockedRequest(UseCaseRequest):
    trainer_id: int
    blocked: bool


@dataclass(kw_only=True)
class SetTrainerBlockedUseCase(UseCase[SetTrainerBlockedRequest, Trainer]):
    """Блокировка тренера админом: is_active=False закрывает ему кабинет, а его
    клиентам — запись и заявки; календарь тренера перестаёт генерироваться."""

    trainer_repo: TrainerRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: SetTrainerBlockedRequest) -> Trainer:
        trainer = await self.trainer_repo.get_by_id(command.trainer_id)
        if trainer is None:
            raise TrainerNotFoundException(trainer_id=command.trainer_id)

        trainer.is_active = not command.blocked
        trainer.touch()
        saved = await self.trainer_repo.save(trainer)
        await self.transaction_manager.commit()

        await self.notification_service.send(
            chat_id=trainer.tg_id,
            text=(
                "⛔ Ваш доступ к кабинету тренера ограничен администратором."
                if command.blocked
                else "✅ Доступ к кабинету тренера восстановлен — /trainer"
            ),
        )
        logger.info(
            "[SetTrainerBlocked:done] trainer_id=%s blocked=%s", trainer.id, command.blocked
        )
        return saved
