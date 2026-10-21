from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.booking import Booking
from src.domain.exception.booking import BookingNotFoundException
from src.domain.repositories.booking import BookingRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager
from src.utils.get_datetime_utc_now import get_aware_utc_now


@dataclass(frozen=True, eq=False)
class MarkBookingsPaidRequest(UseCaseRequest):
    """Тренер отмечает оплату разовых тренировок (наличные/перевод)."""

    trainer_id: int
    booking_ids: tuple[int, ...]
    paid: bool = True


@dataclass(kw_only=True)
class MarkBookingsPaidUseCase(UseCase[MarkBookingsPaidRequest, list[Booking]]):
    booking_repo: BookingRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: MarkBookingsPaidRequest) -> list[Booking]:
        now = get_aware_utc_now()
        saved = []
        for booking_id in command.booking_ids:
            booking = await self.booking_repo.get_by_id(booking_id)
            if booking is None or booking.trainer_id != command.trainer_id:
                raise BookingNotFoundException(booking_id)
            booking.paid_at = now if command.paid else None
            booking.touch()
            saved.append(await self.booking_repo.save(booking))
        await self.transaction_manager.commit()
        return saved
