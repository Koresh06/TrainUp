from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.client import Client
from src.domain.exception.client import ClientNotFoundException
from src.domain.repositories.client import ClientRepository


@dataclass(frozen=True, eq=False)
class GetClientByTgIdRequest(UseCaseRequest):
    tg_id: int


@dataclass(kw_only=True)
class GetClientByTgIdUseCase(UseCase[GetClientByTgIdRequest, Client]):
    client_repo: ClientRepository

    async def __call__(self, command: GetClientByTgIdRequest) -> Client:
        client = await self.client_repo.get_by_tg_id(command.tg_id)
        if client is None:
            raise ClientNotFoundException(tg_id=command.tg_id)
        return client