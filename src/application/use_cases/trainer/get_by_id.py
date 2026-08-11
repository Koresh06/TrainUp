from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.trainer import Trainer
from src.domain.exception.trainer import TrainerNotFoundException
from src.domain.repositories.trainer import TrainerRepository


@dataclass(frozen=True, eq=False)
class GetTrainerByIdRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class GetTrainerByIdUseCase(UseCase[GetTrainerByIdRequest, Trainer]):
    trainer_repo: TrainerRepository

    async def __call__(self, command: GetTrainerByIdRequest) -> Trainer:
        trainer = await self.trainer_repo.get_by_id(command.trainer_id)
        if trainer is None:
            raise TrainerNotFoundException(trainer_id=command.trainer_id)
        return trainer