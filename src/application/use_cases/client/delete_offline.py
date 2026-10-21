import logging
from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.client._shared import get_trainer_client
from src.domain.exception.client import ClientHasBookingsException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.recurring_booking import RecurringBookingRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class DeleteOfflineClientRequest(UseCaseRequest):
    trainer_id: int
    client_id: int


@dataclass(kw_only=True)
class DeleteOfflineClientUseCase(UseCase[DeleteOfflineClientRequest, None]):
    """
    Удалить можно только карточку без Telegram и без истории — это исправление
    ошибки («завёл не того»). Клиента с тренировками удалять нельзя: пропадут
    статистика и учёт оплат.
    """

    client_repo: ClientRepository
    booking_repo: BookingRepository
    recurring_repo: RecurringBookingRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: DeleteOfflineClientRequest) -> None:
        client = await get_trainer_client(
            self.client_repo, client_id=command.client_id, trainer_id=command.trainer_id
        )
        recurring = await self.recurring_repo.get_active_by_trainer_and_client(
            trainer_id=command.trainer_id, client_id=client.id
        )
        if (
            client.has_telegram
            or recurring
            or await self.booking_repo.has_any_by_client(client.id)
        ):
            raise ClientHasBookingsException(client_id=client.id)

        await self.client_repo.delete(client.id)
        await self.transaction_manager.commit()
        logger.info("[DeleteOfflineClient:done] client_id=%s", client.id)
