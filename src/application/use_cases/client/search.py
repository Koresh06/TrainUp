from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.client import Client
from src.domain.repositories.client import ClientRepository


@dataclass(frozen=True, eq=False)
class SearchClientsRequest(UseCaseRequest):
    query: str
    limit: int = 20


@dataclass(kw_only=True)
class SearchClientsUseCase(UseCase[SearchClientsRequest, list[Client]]):
    client_repo: ClientRepository

    async def __call__(self, command: SearchClientsRequest) -> list[Client]:
        return await self.client_repo.search(command.query, command.limit)
