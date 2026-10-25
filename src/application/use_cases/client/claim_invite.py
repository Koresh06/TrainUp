import logging
from dataclasses import dataclass
from html import escape

from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.client import Client
from src.domain.exception.client import (
    ClientAlreadyExistsException,
    ClientInviteNotFoundException,
)
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class ClaimClientInviteRequest(UseCaseRequest):
    token: str
    tg_id: int
    username: str | None


@dataclass(kw_only=True)
class ClaimClientInviteUseCase(UseCase[ClaimClientInviteRequest, Client]):
    """
    Человек открыл персональную ссылку из карточки «клиента без Telegram» —
    привязываем карточку к его аккаунту. Расписание, постоянные записи и
    история остаются, а с этого момента бот шлёт ему напоминания.
    """

    client_repo: ClientRepository
    trainer_repo: TrainerRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: ClaimClientInviteRequest) -> Client:
        client = await self.client_repo.get_by_invite_token(command.token)
        if client is None:
            raise ClientInviteNotFoundException(token=command.token)

        # у этого Telegram уже есть своя карточка — склеивать две истории
        # автоматически не беремся, пусть решает тренер
        if await self.client_repo.get_by_tg_id(command.tg_id) is not None:
            raise ClientAlreadyExistsException(tg_id=command.tg_id)

        client.link_telegram(tg_id=command.tg_id, username=command.username)
        saved = await self.client_repo.save(client)
        await self.transaction_manager.commit()

        trainer = await self.trainer_repo.get_by_id(client.trainer_id)
        if trainer is not None:
            await self.notification_service.send(
                chat_id=trainer.notification_chat_id,
                fallback_chat_id=trainer.tg_id,
                text=(
                    f"🔗 <b>{escape(saved.full_name)}</b> подключился к боту по "
                    f"персональной ссылке — теперь он будет получать напоминания "
                    f"о тренировках."
                ),
            )
        logger.info("[ClaimClientInvite:done] client_id=%s", saved.id)
        return saved
