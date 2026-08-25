from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.trainer import Trainer
from src.domain.exception.trainer import TrainerNotFoundException
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class UpdateTrainerProfileRequest(UseCaseRequest):
    trainer_id: int
    location: str | None = None
    photo_file_id: str | None = None
    social_links: dict[str, str] | None = None


@dataclass(kw_only=True)
class UpdateTrainerProfileUseCase(UseCase[UpdateTrainerProfileRequest, Trainer]):
    trainer_repo: TrainerRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: UpdateTrainerProfileRequest) -> Trainer:
        trainer = await self.trainer_repo.get_by_id(command.trainer_id)
        if trainer is None:
            raise TrainerNotFoundException(trainer_id=command.trainer_id)

        if command.location is not None:
            trainer.location = command.location
        if command.photo_file_id is not None:
            trainer.photo_file_id = command.photo_file_id
        if command.social_links is not None:
            trainer.social_links = command.social_links

        saved = await self.trainer_repo.save(trainer)
        await self.transaction_manager.commit()
        return saved
