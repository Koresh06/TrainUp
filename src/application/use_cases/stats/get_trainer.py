from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.stats.period import StatsPeriod, period_dates
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.recurring_booking import RecurringBookingRepository


@dataclass(frozen=True, eq=False)
class GetTrainerStatsRequest(UseCaseRequest):
    trainer_id: int
    period: StatsPeriod = StatsPeriod.MONTH


@dataclass(frozen=True)
class TrainerStatsDTO:
    total_clients: int
    completed_trainings: int
    cancelled_bookings: int
    upcoming_bookings: int
    recurring_clients: int


@dataclass(kw_only=True)
class GetTrainerStatsUseCase(UseCase[GetTrainerStatsRequest, TrainerStatsDTO]):
    client_repo: ClientRepository
    booking_repo: BookingRepository
    recurring_repo: RecurringBookingRepository

    async def __call__(self, command: GetTrainerStatsRequest) -> TrainerStatsDTO:
        date_from, today = period_dates(command.period)

        clients = await self.client_repo.get_by_trainer_id(command.trainer_id)
        upcoming = await self.booking_repo.get_upcoming_by_trainer(command.trainer_id)
        recurring = await self.recurring_repo.get_active_by_trainer_id(
            command.trainer_id
        )

        completed = await self.booking_repo.count_completed_by_trainer_in_period(
            command.trainer_id, date_from, today
        )
        cancelled = await self.booking_repo.count_cancelled_by_trainer_in_period(
            command.trainer_id, date_from, today
        )

        return TrainerStatsDTO(
            total_clients=len(clients),
            completed_trainings=completed,
            cancelled_bookings=cancelled,
            upcoming_bookings=len(upcoming),
            recurring_clients=len(recurring),
        )
