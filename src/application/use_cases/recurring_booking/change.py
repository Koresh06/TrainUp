from dataclasses import dataclass


from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.booking.reschedule import (
    RescheduleBookingRequest,
    RescheduleBookingUseCase,
)
from src.domain.entities.recurring_booking import RecurringBooking
from src.domain.enums.booking import BookingStatus
from src.domain.exception.calendar_slot import CalendarSlotNotFoundException
from src.domain.exception.recurring_booking import RecurringBookingNotFoundException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.recurring_booking import RecurringBookingRepository
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

        # обновляем сам паттерн — будущие недели пойдут по новому графику
        recurring.weekday = new_slot.slot_date.weekday()
        recurring.start_time = new_slot.start_time
        await self.recurring_repo.save(recurring)
        await self.transaction_manager.commit()

        # переносим ближайшую уже созданную активную тренировку тоже
        latest = await self.booking_repo.get_latest_by_recurring_booking_id(
            recurring.id
        )
        if latest is not None and latest.status in (
            BookingStatus.PENDING,
            BookingStatus.CONFIRMED,
        ):
            await self.reschedule_use_case(
                RescheduleBookingRequest(
                    booking_id=latest.id,
                    new_slot_id=command.new_slot_id,
                )
            )

        return recurring
