from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.stats.period import (
    StatsPeriod,
    period_dates,
    period_datetimes,
)
from src.domain.entities.trainer import Trainer
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.booking import BookingStatus
from src.domain.enums.subscription import PAID_SUBSCRIPTION_SOURCES
from src.domain.exception.trainer import TrainerNotFoundException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.consultation import ConsultationRequestRepository
from src.domain.repositories.feedback import FeedbackRepository
from src.domain.repositories.program import ProgramRequestRepository
from src.domain.repositories.recurring_booking import RecurringBookingRepository
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.trainer import TrainerRepository


@dataclass(frozen=True)
class AdminTrainerReportDTO:
    trainer: Trainer
    period: StatsPeriod
    subscription: TrainerSubscription | None  # самая длинная действующая
    last_subscription: TrainerSubscription | None  # последняя по дате оформления
    clients_total: int
    clients_new: int
    recurring_clients: int
    trainings_completed: int
    trainings_cancelled: int
    trainings_active: int
    requests_total: int
    paid_total: Decimal
    payments_count: int


@dataclass(frozen=True, eq=False)
class GetAdminTrainerReportRequest(UseCaseRequest):
    trainer_id: int
    period: StatsPeriod = StatsPeriod.MONTH


@dataclass(kw_only=True)
class GetAdminTrainerReportUseCase(
    UseCase[GetAdminTrainerReportRequest, AdminTrainerReportDTO]
):
    trainer_repo: TrainerRepository
    client_repo: ClientRepository
    booking_repo: BookingRepository
    recurring_repo: RecurringBookingRepository
    subscription_repo: TrainerSubscriptionRepository
    program_repo: ProgramRequestRepository
    consultation_repo: ConsultationRequestRepository
    feedback_repo: FeedbackRepository

    async def __call__(self, command: GetAdminTrainerReportRequest) -> AdminTrainerReportDTO:
        trainer = await self.trainer_repo.get_by_id(command.trainer_id)
        if trainer is None:
            raise TrainerNotFoundException(trainer_id=command.trainer_id)

        date_from, date_to = period_dates(command.period)
        start, end = period_datetimes(command.period)

        clients = await self.client_repo.get_by_trainer_id(trainer.id)
        recurring = await self.recurring_repo.get_active_by_trainer_id(trainer.id)
        subscriptions = await self.subscription_repo.get_by_trainer_id(trainer.id)
        active = await self.subscription_repo.get_active_by_trainer_id(trainer.id)
        bookings_by = await self.booking_repo.count_by_trainer_and_status(date_from, date_to)

        def bookings_count(*statuses: BookingStatus) -> int:
            return sum(bookings_by.get((trainer.id, status), 0) for status in statuses)

        requests_total = 0
        for repo in (self.program_repo, self.consultation_repo, self.feedback_repo):
            counts = await repo.count_by_trainer_created_between(start, end)
            requests_total += counts.get(trainer.id, 0)

        paid = [s for s in subscriptions if s.source in PAID_SUBSCRIPTION_SOURCES]

        def created(dt: datetime) -> datetime:
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

        return AdminTrainerReportDTO(
            trainer=trainer,
            period=command.period,
            subscription=active,
            last_subscription=subscriptions[0] if subscriptions else None,
            clients_total=len(clients),
            clients_new=sum(1 for c in clients if start <= created(c.created_at) < end),
            recurring_clients=len({r.client_id for r in recurring}),
            trainings_completed=bookings_count(BookingStatus.COMPLETED),
            trainings_cancelled=bookings_count(BookingStatus.CANCELLED),
            trainings_active=bookings_count(BookingStatus.PENDING, BookingStatus.CONFIRMED),
            requests_total=requests_total,
            paid_total=sum((s.amount for s in paid), Decimal("0")),
            payments_count=len(paid),
        )
