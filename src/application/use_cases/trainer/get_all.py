from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.trainer import Trainer
from src.domain.repositories.trainer import TrainerRepository


@dataclass(frozen=True, eq=False)
class GetAllTrainersRequest(UseCaseRequest):
    pass


@dataclass(kw_only=True)
class GetAllTrainersUseCase(UseCase[GetAllTrainersRequest, list[Trainer]]):
    trainer_repo: TrainerRepository

    async def __call__(self, command: GetAllTrainersRequest) -> list[Trainer]:
        trainers = await self.trainer_repo.get_all()
        return sorted(trainers, key=lambda t: t.id)
