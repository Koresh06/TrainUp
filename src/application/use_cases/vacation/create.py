import logging
from dataclasses import dataclass
from datetime import date

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.booking.cancel import (
    CancelBookingRequest,
    CancelBookingUseCase,
    CancelInitiator,
)
from src.application.use_cases.vacation._shared import period_slots_and_bookings
from src.application.use_cases.vacation.preview import VacationPreviewDTO
from src.domain.entities.trainer_vacation import TrainerVacation
from src.domain.enums.slot import SlotStatus
from src.domain.exception.vacation import InvalidVacationPeriodException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.trainer_vacation import TrainerVacationRepository
from src.domain.services.calendar_service import CalendarService
from src.domain.utils import get_project_today
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class CreateVacationRequest(UseCaseRequest):
    trainer_id: int
    date_from: date
    date_to: date
    note: str | None = None


@dataclass(kw_only=True)
class CreateVacationUseCase(UseCase[CreateVacationRequest, VacationPreviewDTO]):
    """
    Отпуск/больничный: закрываем все слоты периода, отменяем записи (клиенты в
    Telegram получают сообщение с датами отпуска) и запоминаем период — слоты,
    которые календарь сгенерирует позже, тоже будут закрыты.
    """

    vacation_repo: TrainerVacationRepository
    slot_repo: CalendarSlotRepository
    booking_repo: BookingRepository
    calendar_service: CalendarService
    cancel_booking: CancelBookingUseCase
    transaction_manager: TransactionManager

    async def __call__(self, command: CreateVacationRequest) -> VacationPreviewDTO:
        if command.date_to < command.date_from or command.date_to < get_project_today():
            raise InvalidVacationPeriodException()

        await self.vacation_repo.save(
            TrainerVacation(
                trainer_id=command.trainer_id,
                date_from=command.date_from,
                date_to=command.date_to,
                note=command.note,
            )
        )
        slots, views = await period_slots_and_bookings(
            trainer_id=command.trainer_id,
            date_from=command.date_from,
            date_to=command.date_to,
            slot_repo=self.slot_repo,
            booking_repo=self.booking_repo,
        )
        blocked = 0
        for slot in slots:
            if slot.status != SlotStatus.BLOCKED:
                await self.calendar_service.block_slot(slot.id)
                blocked += 1
        await self.transaction_manager.commit()

        period = f"{command.date_from.strftime('%d.%m')}–{command.date_to.strftime('%d.%m')}"
        for view in views:
            await self.cancel_booking(
                CancelBookingRequest(
                    booking_id=view.booking.id,
                    initiated_by=CancelInitiator.TRAINER,
                    client_message=(
                        f"🏖 С {period} тренер не проводит тренировки. "
                        f"Выберите, пожалуйста, другое время."
                    ),
                )
            )

        logger.info(
            "[CreateVacation:done] trainer_id=%s %s blocked=%s cancelled=%s",
            command.trainer_id, period, blocked, len(views),
        )
        return VacationPreviewDTO(slots_to_block=blocked, bookings=views)
