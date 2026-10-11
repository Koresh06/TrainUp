import logging
from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.client import Client
from src.domain.exception.client import ClientNotFoundException
from src.domain.repositories.client import ClientRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class SetClientBlockedRequest(UseCaseRequest):
    client_id: int
    blocked: bool


@dataclass(kw_only=True)
class SetClientBlockedUseCase(UseCase[SetClientBlockedRequest, Client]):
    client_repo: ClientRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: SetClientBlockedRequest) -> Client:
        client = await self.client_repo.get_by_id(command.client_id)
        if client is None:
            raise ClientNotFoundException(client_id=command.client_id)

        client.is_active = not command.blocked
        client.touch()
        saved = await self.client_repo.save(client)
        await self.transaction_manager.commit()

        logger.info(
            "[SetClientBlocked:done] client_id=%s blocked=%s", client.id, command.blocked
        )
        return saved
