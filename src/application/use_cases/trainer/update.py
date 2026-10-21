import logging
from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.trainer import Trainer
from src.domain.exception.trainer import TrainerNotFoundException
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class UpdateTrainerProfileRequest(UseCaseRequest):
    """None — поле не менять; для фото есть отдельный флаг удаления."""

    trainer_id: int
    name: str | None = None
    bio: str | None = None
    phone: str | None = None
    photo_file_id: str | None = None
    remove_photo: bool = False
    social_links: dict[str, str] | None = None
    notification_chat_id: int | None = None


@dataclass(kw_only=True)
class UpdateTrainerProfileUseCase(UseCase[UpdateTrainerProfileRequest, Trainer]):
    trainer_repo: TrainerRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: UpdateTrainerProfileRequest) -> Trainer:
        trainer = await self.trainer_repo.get_by_id(command.trainer_id)
        if trainer is None:
            raise TrainerNotFoundException(trainer_id=command.trainer_id)

        changed = []
        for field in ("name", "bio", "phone", "photo_file_id", "social_links", "notification_chat_id"):
            value = getattr(command, field)
            if value is not None:
                setattr(trainer, field, value)
                changed.append(field)
        if command.remove_photo:
            trainer.photo_file_id = None
            changed.append("photo_removed")

        saved = await self.trainer_repo.save(trainer)
        await self.transaction_manager.commit()
        logger.info("[UpdateTrainerProfile:done] trainer_id=%s changed=%s", trainer.id, changed)
        return saved
