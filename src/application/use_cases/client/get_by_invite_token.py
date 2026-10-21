from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.client import Client
from src.domain.exception.client import ClientInviteNotFoundException
from src.domain.repositories.client import ClientRepository


@dataclass(frozen=True, eq=False)
class GetClientByInviteTokenRequest(UseCaseRequest):
    token: str


@dataclass(kw_only=True)
class GetClientByInviteTokenUseCase(UseCase[GetClientByInviteTokenRequest, Client]):
    client_repo: ClientRepository

    async def __call__(self, command: GetClientByInviteTokenRequest) -> Client:
        client = await self.client_repo.get_by_invite_token(command.token)
        if client is None:
            raise ClientInviteNotFoundException(token=command.token)
        return client
