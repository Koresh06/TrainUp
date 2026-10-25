import logging
from dataclasses import dataclass
from html import escape

from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.booking import Booking
from src.domain.exception.booking import BookingNotFoundException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)

# оценка ниже или равна — тренер получает сигнал, чтобы разобраться
LOW_RATING = 3


@dataclass(frozen=True, eq=False)
class RateBookingRequest(UseCaseRequest):
    booking_id: int
    client_id: int
    stars: int


@dataclass(kw_only=True)
class RateBookingUseCase(UseCase[RateBookingRequest, Booking]):
    booking_repo: BookingRepository
    client_repo: ClientRepository
    trainer_repo: TrainerRepository
    slot_repo: CalendarSlotRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: RateBookingRequest) -> Booking:
        booking = await self.booking_repo.get_by_id(command.booking_id)
        if booking is None or booking.client_id != command.client_id:
            raise BookingNotFoundException(command.booking_id)
        booking.rate(command.stars)
        saved = await self.booking_repo.save(booking)
        await self.transaction_manager.commit()

        if command.stars <= LOW_RATING:
            client = await self.client_repo.get_by_id(booking.client_id)
            trainer = await self.trainer_repo.get_by_id(booking.trainer_id)
            slot = await self.slot_repo.get_by_id(booking.slot_id)
            if client is not None and trainer is not None and slot is not None:
                await self.notification_service.send(
                    chat_id=trainer.notification_chat_id,
                    fallback_chat_id=trainer.tg_id,
                    text=(
                        f"⚠️ <b>{escape(client.full_name)}</b> оценил тренировку "
                        f"{slot.slot_date.strftime('%d.%m')} в {slot.start_time.strftime('%H:%M')} "
                        f"на {'⭐' * command.stars}\n"
                        f"Стоит узнать, что пошло не так."
                    ),
                )
        logger.info("[RateBooking:done] booking_id=%s stars=%s", booking.id, command.stars)
        return saved
