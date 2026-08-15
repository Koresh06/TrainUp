from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.client import Client
from src.domain.repositories.client import ClientRepository


@dataclass(frozen=True, eq=False)
class GetClientsByTrainerRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class GetClientsByTrainerUseCase(UseCase[GetClientsByTrainerRequest, list[Client]]):
    client_repo: ClientRepository

    async def __call__(self, command: GetClientsByTrainerRequest) -> list[Client]:
        return await self.client_repo.get_by_trainer_id(command.trainer_id)
