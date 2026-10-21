import logging
from dataclasses import dataclass

from src.application.interfaces.booking_scheduler import BookingScheduler
from src.application.services.package_charge import PackageChargeService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.booking import Booking
from src.domain.exception.booking import BookingNotFoundException, TrainingNotStartedException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.utils import get_training_datetime_utc
from src.infrastructure.database.transaction_manager.base import TransactionManager
from src.utils.get_datetime_utc_now import get_datetime_utc_now

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class MarkBookingAttendanceRequest(UseCaseRequest):
    trainer_id: int
    booking_id: int
    # False — «не пришёл», True — исправить ошибочную неявку на «проведена»
    attended: bool


@dataclass(kw_only=True)
class MarkBookingAttendanceUseCase(UseCase[MarkBookingAttendanceRequest, Booking]):
    """
    Отметка неявки. Доступна, когда тренировка уже началась: и до
    автозавершения (CONFIRMED), и после него (COMPLETED). Неявка нужна для
    честной статистики посещаемости и учёта абонементов.
    """

    booking_repo: BookingRepository
    slot_repo: CalendarSlotRepository
    booking_scheduler: BookingScheduler
    package_charge: PackageChargeService
    transaction_manager: TransactionManager

    async def __call__(self, command: MarkBookingAttendanceRequest) -> Booking:
        booking = await self.booking_repo.get_by_id(command.booking_id)
        if booking is None or booking.trainer_id != command.trainer_id:
            raise BookingNotFoundException(command.booking_id)

        if command.attended:
            booking.mark_attended()
        else:
            slot = await self.slot_repo.get_by_id(booking.slot_id)
            if slot is None or get_training_datetime_utc(slot) > get_datetime_utc_now():
                raise TrainingNotStartedException(booking_id=booking.id)
            had_completion_job = booking.completion_job_id is not None
            booking.mark_no_show()
            if had_completion_job:
                # автозавершение уже не нужно — иначе «проведена» перезапишет неявку
                await self.booking_scheduler.cancel_booking_completion(booking_id=booking.id)
                booking.completion_job_id = None

        # неявка может не списывать занятие (настройка тренера) — пересчитываем
        await self.package_charge.sync(booking)
        saved = await self.booking_repo.save(booking)
        await self.transaction_manager.commit()
        logger.info(
            "[MarkBookingAttendance:done] booking_id=%s status=%s", saved.id, saved.status
        )
        return saved
