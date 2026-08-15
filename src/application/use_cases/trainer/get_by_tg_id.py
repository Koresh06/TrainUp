from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.trainer import Trainer
from src.domain.exception.trainer import TrainerNotFoundException
from src.domain.repositories.trainer import TrainerRepository


@dataclass(frozen=True, eq=False)
class GetTrainerByTgIdRequest(UseCaseRequest):
    tg_id: int


@dataclass(kw_only=True)
class GetTrainerByTgIdUseCase(UseCase[GetTrainerByTgIdRequest, Trainer]):
    trainer_repo: TrainerRepository

    async def __call__(self, command: GetTrainerByTgIdRequest) -> Trainer:
        trainer = await self.trainer_repo.get_by_tg_id(command.tg_id)
        if trainer is None:
            raise TrainerNotFoundException(tg_id=command.tg_id)
        return trainer