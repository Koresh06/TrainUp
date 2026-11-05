from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.client import Client
from src.domain.repositories.client import ClientRepository


@dataclass(frozen=True, eq=False)
class GetClientsByTrainerIdRequest(UseCaseRequest):
    trainer_id: int
    # False — текущие клиенты (все списки тренера), True — «🗄 Архив»
    archived: bool = False


@dataclass(kw_only=True)
class GetClientsByTrainerIdUseCase(UseCase[GetClientsByTrainerIdRequest, list[Client]]):
    client_repo: ClientRepository

    async def __call__(self, command: GetClientsByTrainerIdRequest) -> list[Client]:
        clients = await self.client_repo.get_by_trainer_id(command.trainer_id)
        return [c for c in clients if c.is_archived == command.archived]
