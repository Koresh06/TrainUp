from dataclasses import dataclass

from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.booking import Booking
from src.domain.exception.booking import BookingNotFoundException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.client import ClientRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class ConfirmBookingRequest(UseCaseRequest):
    booking_id: int


@dataclass(kw_only=True)
class ConfirmBookingUseCase(UseCase[ConfirmBookingRequest, Booking]):
    booking_repo: BookingRepository
    client_repo: ClientRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: ConfirmBookingRequest) -> Booking:
        booking = await self.booking_repo.get_by_id(command.booking_id)
        if booking is None:
            raise BookingNotFoundException(command.booking_id)

        booking.confirm()
        saved = await self.booking_repo.save(booking)
        await self.transaction_manager.commit()

        client = await self.client_repo.get_by_id(booking.client_id)
        if client is not None:
            await self.notification_service.send(
                chat_id=client.tg_id,
                text="✅ Тренер подтвердил вашу запись!",
            )

        return saved
