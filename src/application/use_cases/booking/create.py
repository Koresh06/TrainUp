import logging
from dataclasses import dataclass

from src.domain.entities.booking import Booking
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.client import Client
from src.domain.entities.trainer import Trainer
from src.domain.enums.booking import BookingStatus
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.services.calendar_service import CalendarService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.interfaces.notification_service import (
    NotificationService,
    NewBookingNotificationDTO,
)
from src.infrastructure.database.transaction_manager.base import TransactionManager


logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class CreateBookingRequest(UseCaseRequest):
    client_id: int
    trainer_id: int
    slot_id: int


@dataclass(kw_only=True)
class CreateBookingUseCase(UseCase[CreateBookingRequest, Booking]):
    calendar_service: CalendarService
    booking_repo: BookingRepository
    trainer_repo: TrainerRepository
    client_repo: ClientRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: CreateBookingRequest) -> Booking:
        logger.info(
            "[CreateBooking] client_id=%s trainer_id=%s slot_id=%s",
            command.client_id,
            command.trainer_id,
            command.slot_id,
        )

        # проверяет доступность и переводит слот в BOOKED;
        # кидает CalendarSlotNotFoundException / SlotAlreadyBookedException
        slot: CalendarSlot = await self.calendar_service.book_slot(command.slot_id)

        booking = Booking(
            client_id=command.client_id,
            trainer_id=command.trainer_id,
            slot_id=command.slot_id,
            status=BookingStatus.PENDING,
        )
        saved = await self.booking_repo.save(booking)
        await self.transaction_manager.commit()

        trainer: Trainer | None = await self.trainer_repo.get_by_id(command.trainer_id)
        client: Client | None = await self.client_repo.get_by_id(command.client_id)
        if trainer is not None and client is not None:
            await self.notification_service.notify_new_booking(
                NewBookingNotificationDTO(
                    chat_id=trainer.notification_chat_id,
                    booking_id=saved.id,
                    date_label=slot.slot_date.strftime("%d.%m.%Y"),
                    time_label=slot.start_time.strftime("%H:%M"),
                    client_first_name=client.first_name,
                    client_last_name=client.last_name,
                    client_username=client.username,
                    client_phone=client.phone,
                    client_age=client.age,
                )
            )

        logger.info("[CreateBooking:done] booking_id=%s", saved.id)
        return saved
