from dataclasses import dataclass

from src.domain.exception.recurring_booking import RecurringBookingNotFoundException
from src.domain.repositories.recurring_booking import RecurringBookingRepository
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class DeactivateRecurringBookingRequest(UseCaseRequest):
    recurring_booking_id: int


@dataclass(kw_only=True)
class DeactivateRecurringBookingUseCase(
    UseCase[DeactivateRecurringBookingRequest, None]
):
    recurring_repo: RecurringBookingRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: DeactivateRecurringBookingRequest) -> None:
        recurring = await self.recurring_repo.get_by_id(command.recurring_booking_id)
        if recurring is None:
            raise RecurringBookingNotFoundException(command.recurring_booking_id)

        recurring.is_active = False
        await self.recurring_repo.save(recurring)
        await self.transaction_manager.commit()
