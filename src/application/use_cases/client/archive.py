import logging
from dataclasses import dataclass
from html import escape

from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.booking.cancel import (
    CancelBookingRequest,
    CancelBookingUseCase,
    CancelInitiator,
)
from src.application.use_cases.client._shared import get_trainer_client
from src.domain.entities.client import Client
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.recurring_booking import RecurringBookingRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.utils import is_slot_in_past
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


def client_archived_text(trainer_name: str) -> str:
    return (
        f"ℹ️ Тренер <b>{escape(trainer_name)}</b> завершил с вами работу в боте, "
        f"запись к нему закрыта.\n\n"
        f"Если снова захотите заниматься у этого тренера, откройте его ссылку "
        f"для записи ещё раз."
    )


@dataclass(frozen=True, eq=False)
class ArchiveClientRequest(UseCaseRequest):
    trainer_id: int
    client_id: int


@dataclass(frozen=True)
class ArchiveClientResultDTO:
    client: Client
    cancelled_bookings: int
    stopped_recurring: int


@dataclass(kw_only=True)
class ArchiveClientUseCase(UseCase[ArchiveClientRequest, ArchiveClientResultDTO]):
    """
    Клиент ушёл от тренера. Карточку не удаляем: проведённые тренировки,
    оплаты и абонементы остаются в статистике и отчётах. Тренер больше не
    видит клиента в списках (только в «🗄 Архиве»), будущие записи и
    постоянное расписание отменяются без отдельных сообщений, а клиент
    получает одно общее сообщение.
    """

    client_repo: ClientRepository
    trainer_repo: TrainerRepository
    booking_repo: BookingRepository
    recurring_repo: RecurringBookingRepository
    cancel_use_case: CancelBookingUseCase
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: ArchiveClientRequest) -> ArchiveClientResultDTO:
        client = await get_trainer_client(
            self.client_repo, client_id=command.client_id, trainer_id=command.trainer_id
        )
        if client.is_archived:
            return ArchiveClientResultDTO(client=client, cancelled_bookings=0, stopped_recurring=0)

        # сначала шаблоны постоянки: иначе поддержка буфера успеет создать
        # новую тренировку по шаблону, пока мы отменяем старые
        recurring = await self.recurring_repo.get_active_by_trainer_and_client(
            trainer_id=command.trainer_id, client_id=client.id
        )
        for item in recurring:
            item.is_active = False
            await self.recurring_repo.save(item)

        client.archive()
        saved = await self.client_repo.save(client)
        await self.transaction_manager.commit()

        cancelled = 0
        for booking in await self.booking_repo.get_upcoming_by_client(client.id):
            slot = await self.cancel_use_case.slot_repo.get_by_id(booking.slot_id)
            if slot is not None and is_slot_in_past(slot):
                continue  # уже идёт/прошла — её закроет автозавершение
            await self.cancel_use_case(
                CancelBookingRequest(
                    booking_id=booking.id,
                    initiated_by=CancelInitiator.TRAINER,
                    notify=False,
                )
            )
            cancelled += 1

        trainer = await self.trainer_repo.get_by_id(command.trainer_id)
        if trainer is not None and client.has_telegram and client.is_active:
            await self.notification_service.send(
                chat_id=client.tg_id, text=client_archived_text(trainer.name)
            )

        logger.info(
            "[ArchiveClient:done] client_id=%s trainer_id=%s cancelled=%s recurring=%s",
            client.id, command.trainer_id, cancelled, len(recurring),
        )
        return ArchiveClientResultDTO(
            client=saved, cancelled_bookings=cancelled, stopped_recurring=len(recurring)
        )


@dataclass(frozen=True, eq=False)
class RestoreClientRequest(UseCaseRequest):
    trainer_id: int
    client_id: int
    # клиент сам вернулся по ссылке тренера — тренеру приходит сообщение;
    # если вернул сам тренер из архива, сообщать ему незачем
    by_client: bool = False


@dataclass(kw_only=True)
class RestoreClientUseCase(UseCase[RestoreClientRequest, Client]):
    """Вернуть клиента из архива: снова виден тренеру и может записываться.
    Отменённые при архивации записи не восстанавливаются."""

    client_repo: ClientRepository
    trainer_repo: TrainerRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: RestoreClientRequest) -> Client:
        client = await get_trainer_client(
            self.client_repo, client_id=command.client_id, trainer_id=command.trainer_id
        )
        if not client.is_archived:
            return client

        client.restore()
        saved = await self.client_repo.save(client)
        await self.transaction_manager.commit()

        if command.by_client:
            trainer = await self.trainer_repo.get_by_id(command.trainer_id)
            if trainer is not None:
                await self.notification_service.send(
                    chat_id=trainer.notification_chat_id,
                    fallback_chat_id=trainer.tg_id,
                    text=(
                        f"↩️ Клиент <b>{escape(client.full_name)}</b> снова открыл вашу "
                        f"ссылку и вернулся из архива — он опять в «👥 Мои клиенты» "
                        f"и может записываться."
                    ),
                )

        logger.info(
            "[RestoreClient:done] client_id=%s trainer_id=%s by_client=%s",
            client.id, command.trainer_id, command.by_client,
        )
        return saved
