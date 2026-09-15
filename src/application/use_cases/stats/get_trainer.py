from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.recurring_booking import RecurringBookingRepository


class StatsPeriod(str, Enum):
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    ALL = "all"


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
        today = date.today()

        if command.period == StatsPeriod.TODAY:
            date_from = today
        elif command.period == StatsPeriod.WEEK:
            date_from = today - timedelta(days=today.weekday())
        elif command.period == StatsPeriod.MONTH:
            date_from = today.replace(day=1)
        else:
            date_from = date(2000, 1, 1)

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
