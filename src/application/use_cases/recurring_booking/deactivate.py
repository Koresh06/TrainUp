import logging
from dataclasses import dataclass

from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.booking.cancel import (
    CancelBookingRequest,
    CancelBookingUseCase,
    CancelInitiator,
)
from src.domain.constants import WEEKDAY_LABELS_EVERY
from src.domain.exception.recurring_booking import RecurringBookingNotFoundException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.recurring_booking import RecurringBookingRepository
from src.domain.utils import is_slot_in_past
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class DeactivateRecurringBookingRequest(UseCaseRequest):
    recurring_booking_id: int


@dataclass(kw_only=True)
class DeactivateRecurringBookingUseCase(
    UseCase[DeactivateRecurringBookingRequest, None]
):
    """
    Остановка постоянной записи отменяет её целиком: шаблон деактивируется,
    а уже созданные будущие тренировки по нему отменяются (клиент получает
    уведомление). Чтобы сменить дни/время — «Изменить день/время», а не стоп.
    """

    recurring_repo: RecurringBookingRepository
    booking_repo: BookingRepository
    client_repo: ClientRepository
    cancel_use_case: CancelBookingUseCase
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: DeactivateRecurringBookingRequest) -> None:
        recurring = await self.recurring_repo.get_by_id(command.recurring_booking_id)
        if recurring is None:
            raise RecurringBookingNotFoundException(command.recurring_booking_id)

        recurring.is_active = False
        await self.recurring_repo.save(recurring)
        await self.transaction_manager.commit()

        upcoming = await self.booking_repo.get_upcoming_by_recurring_booking_id(
            recurring.id
        )
        cancelled = 0
        for booking in upcoming:
            slot = await self.cancel_use_case.slot_repo.get_by_id(booking.slot_id)
            if slot is not None and is_slot_in_past(slot):
                continue  # уже идёт/прошла — её закроет автозавершение
            await self.cancel_use_case(
                CancelBookingRequest(
                    booking_id=booking.id, initiated_by=CancelInitiator.TRAINER
                )
            )
            cancelled += 1

        client = await self.client_repo.get_by_id(recurring.client_id)
        if client is not None:
            await self.notification_service.send(
                chat_id=client.tg_id,
                text=(
                    f"🛑 <b>Постоянная запись остановлена</b>\n\n"
                    f"Тренировки {WEEKDAY_LABELS_EVERY[recurring.weekday]} "
                    f"в {recurring.start_time.strftime('%H:%M')} больше не будут "
                    f"создаваться автоматически."
                ),
            )

        logger.info(
            "[DeactivateRecurringBooking:done] id=%s cancelled_bookings=%s",
            recurring.id, cancelled,
        )
