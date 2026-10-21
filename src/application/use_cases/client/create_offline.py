import logging
from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.client._shared import new_client_invite_token
from src.domain.entities.client import Client
from src.domain.enums.client import ClientSource
from src.domain.repositories.client import ClientRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class CreateOfflineClientRequest(UseCaseRequest):
    trainer_id: int
    first_name: str
    last_name: str | None = None
    phone: str | None = None
    trainer_note: str | None = None


@dataclass(kw_only=True)
class CreateOfflineClientUseCase(UseCase[CreateOfflineClientRequest, Client]):
    """
    Карточка клиента без Telegram: тренер ведёт его расписание и учёт сам,
    бот такому клиенту ничего не отправляет. Сразу выдаём токен персональной
    ссылки — если человек позже придёт в бота, он «заберёт» карточку с историей.
    """

    client_repo: ClientRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: CreateOfflineClientRequest) -> Client:
        client = Client(
            trainer_id=command.trainer_id,
            first_name=command.first_name.strip(),
            last_name=(command.last_name or "").strip() or None,
            phone=command.phone,
            trainer_note=command.trainer_note,
            source=ClientSource.MANUAL,
            invite_token=new_client_invite_token(),
        )
        saved = await self.client_repo.save(client)
        await self.transaction_manager.commit()
        logger.info(
            "[CreateOfflineClient:done] client_id=%s trainer_id=%s", saved.id, command.trainer_id
        )
        return saved
