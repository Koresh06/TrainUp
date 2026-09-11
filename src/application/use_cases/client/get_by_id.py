from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.client import Client
from src.domain.exception.client import ClientNotFoundException
from src.domain.repositories.client import ClientRepository


@dataclass(frozen=True, eq=False)
class GetClientByIdRequest(UseCaseRequest):
    client_id: int


@dataclass(kw_only=True)
class GetClientByIdUseCase(UseCase[GetClientByIdRequest, Client]):
    client_repo: ClientRepository

    async def __call__(self, command: GetClientByIdRequest) -> Client:
        client = await self.client_repo.get_by_id(command.client_id)
        if client is None:
            raise ClientNotFoundException(client_id=command.client_id)
        return client