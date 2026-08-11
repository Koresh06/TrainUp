import logging
from dataclasses import dataclass

from src.domain.entities.booking import Booking
from src.domain.enums.booking import BookingStatus
from src.domain.repositories.booking import BookingRepository
from src.domain.services.calendar_service import CalendarService
from src.application.use_cases.base import UseCase, UseCaseRequest
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
    transaction_manager: TransactionManager

    async def __call__(self, command: CreateBookingRequest) -> Booking:
        logger.info(
            "[CreateBooking] client_id=%s trainer_id=%s slot_id=%s",
            command.client_id, command.trainer_id, command.slot_id,
        )

        # проверяет доступность и переводит слот в BOOKED;
        # кидает CalendarSlotNotFoundException / SlotAlreadyBookedException
        await self.calendar_service.book_slot(command.slot_id)

        booking = Booking(
            client_id=command.client_id,
            trainer_id=command.trainer_id,
            slot_id=command.slot_id,
            status=BookingStatus.PENDING,
        )
        saved = await self.booking_repo.save(booking)
        await self.transaction_manager.commit()

        logger.info("[CreateBooking:done] booking_id=%s", saved.id)
        return saved