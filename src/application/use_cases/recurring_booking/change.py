from dataclasses import dataclass


from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.booking.reschedule import (
    RescheduleBookingRequest,
    RescheduleBookingUseCase,
)
from src.domain.entities.recurring_booking import RecurringBooking
from src.domain.exception.calendar_slot import CalendarSlotNotFoundException
from src.domain.exception.recurring_booking import (
    RecurringBookingAlreadyExistsException,
    RecurringBookingNotFoundException,
)
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.recurring_booking import RecurringBookingRepository
from src.domain.utils import is_slot_in_past
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class ChangeRecurringBookingScheduleRequest(UseCaseRequest):
    recurring_booking_id: int
    new_slot_id: int


@dataclass(kw_only=True)
class ChangeRecurringBookingScheduleUseCase(
    UseCase[ChangeRecurringBookingScheduleRequest, RecurringBooking]
):
    recurring_repo: RecurringBookingRepository
    booking_repo: BookingRepository
    reschedule_use_case: RescheduleBookingUseCase
    transaction_manager: TransactionManager

    async def __call__(
        self, command: ChangeRecurringBookingScheduleRequest
    ) -> RecurringBooking:
        recurring = await self.recurring_repo.get_by_id(command.recurring_booking_id)
        if recurring is None:
            raise RecurringBookingNotFoundException(command.recurring_booking_id)

        new_slot = await self.reschedule_use_case.slot_repo.get_by_id(
            command.new_slot_id
        )
        if new_slot is None:
            raise CalendarSlotNotFoundException(command.new_slot_id)

        new_weekday = new_slot.slot_date.weekday()
        pattern_changed = (
            recurring.weekday != new_weekday
            or recurring.start_time != new_slot.start_time
        )
        if pattern_changed and await self.recurring_repo.exists_active(
            trainer_id=recurring.trainer_id,
            client_id=recurring.client_id,
            weekday=new_weekday,
            start_time=new_slot.start_time,
        ):
            raise RecurringBookingAlreadyExistsException(
                trainer_id=recurring.trainer_id,
                client_id=recurring.client_id,
                weekday=new_weekday,
                start_time=new_slot.start_time,
            )

        # сначала переносим ближайшую ещё не прошедшую тренировку — если перенос
        # упадёт (слот заблокирован/прошёл), шаблон останется прежним и данные
        # не разъедутся
        latest = await self.booking_repo.get_latest_by_recurring_booking_id(
            recurring.id
        )
        if latest is not None and latest.is_active():
            latest_slot = await self.reschedule_use_case.slot_repo.get_by_id(
                latest.slot_id
            )
            if latest_slot is not None and not is_slot_in_past(latest_slot):
                await self.reschedule_use_case(
                    RescheduleBookingRequest(
                        booking_id=latest.id,
                        new_slot_id=command.new_slot_id,
                        force=True,
                    )
                )

        # обновляем сам паттерн — будущие недели пойдут по новому графику
        recurring.weekday = new_weekday
        recurring.start_time = new_slot.start_time
        await self.recurring_repo.save(recurring)
        await self.transaction_manager.commit()

        return recurring
