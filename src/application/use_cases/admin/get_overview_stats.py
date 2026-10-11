from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.stats.period import (
    StatsPeriod,
    period_dates,
    period_datetimes,
)
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.booking import BookingStatus
from src.domain.enums.payment import PaymentMethod, PaymentStatus
from src.domain.enums.subscription import PAID_SUBSCRIPTION_SOURCES, SubscriptionSource
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.consultation import ConsultationRequestRepository
from src.domain.repositories.feedback import FeedbackRepository
from src.domain.repositories.payment import PaymentRepository
from src.domain.repositories.program import ProgramRequestRepository
from src.domain.repositories.recurring_booking import RecurringBookingRepository
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.trainer import TrainerRepository


@dataclass(frozen=True)
class TopTrainerDTO:
    trainer_id: int
    name: str
    completed: int


@dataclass(frozen=True)
class AdminOverviewStatsDTO:
    period: StatsPeriod
    # тренеры
    trainers_total: int
    trainers_new: int
    trainers_blocked: int
    trainers_with_subscription: int
    # клиенты
    clients_total: int
    clients_new: int
    clients_blocked: int
    recurring_active: int
    # тренировки (по дате тренировки в периоде)
    trainings_completed: int
    trainings_cancelled: int
    trainings_active: int
    # заявки (созданные в периоде)
    requests_program: int
    requests_consultation: int
    requests_feedback: int
    # оплаты подписок (созданные в периоде)
    revenue_period: Decimal
    revenue_purchase: Decimal
    revenue_cash: Decimal
    payments_count: int
    trials_count: int
    revenue_all_time: Decimal
    top_trainers: list[TopTrainerDTO] = field(default_factory=list)
    # оплаченные платежи за период по способам: метод -> (количество, сумма $)
    payments_by_method: dict[PaymentMethod, tuple[int, Decimal]] = field(default_factory=dict)


def _in_range(dt: datetime, start: datetime, end: datetime) -> bool:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return start <= dt < end


def _sum_amount(subscriptions: list[TrainerSubscription]) -> Decimal:
    return sum((s.amount for s in subscriptions), Decimal("0"))


@dataclass(frozen=True, eq=False)
class GetAdminOverviewStatsRequest(UseCaseRequest):
    period: StatsPeriod = StatsPeriod.MONTH


@dataclass(kw_only=True)
class GetAdminOverviewStatsUseCase(
    UseCase[GetAdminOverviewStatsRequest, AdminOverviewStatsDTO]
):
    trainer_repo: TrainerRepository
    client_repo: ClientRepository
    booking_repo: BookingRepository
    recurring_repo: RecurringBookingRepository
    subscription_repo: TrainerSubscriptionRepository
    program_repo: ProgramRequestRepository
    consultation_repo: ConsultationRequestRepository
    feedback_repo: FeedbackRepository
    payment_repo: PaymentRepository

    async def __call__(self, command: GetAdminOverviewStatsRequest) -> AdminOverviewStatsDTO:
        date_from, date_to = period_dates(command.period)
        start, end = period_datetimes(command.period)
        now = datetime.now(timezone.utc)

        trainers = await self.trainer_repo.get_all()
        clients = await self.client_repo.get_all()
        subscriptions = await self.subscription_repo.get_all()
        recurring = await self.recurring_repo.get_all_active()
        bookings_by = await self.booking_repo.count_by_trainer_and_status(date_from, date_to)

        def bookings_count(*statuses: BookingStatus) -> int:
            return sum(c for (_, status), c in bookings_by.items() if status in statuses)

        active_trainer_ids = {s.trainer_id for s in subscriptions if s.is_active(now)}
        paid = [s for s in subscriptions if s.source in PAID_SUBSCRIPTION_SOURCES]
        paid_period = [s for s in paid if _in_range(s.created_at, start, end)]
        trials_period = [
            s for s in subscriptions
            if s.source == SubscriptionSource.TRIAL and _in_range(s.created_at, start, end)
        ]

        completed_by_trainer: dict[int, int] = {}
        for (trainer_id, status), count in bookings_by.items():
            if status == BookingStatus.COMPLETED:
                completed_by_trainer[trainer_id] = count
        names = {t.id: t.name for t in trainers}
        top = sorted(completed_by_trainer.items(), key=lambda kv: kv[1], reverse=True)[:5]

        payments_by_method: dict[PaymentMethod, tuple[int, Decimal]] = {}
        for payment in await self.payment_repo.get_all():
            if payment.status != PaymentStatus.PAID or payment.paid_at is None:
                continue
            if not _in_range(payment.paid_at, start, end):
                continue
            count, total = payments_by_method.get(payment.method, (0, Decimal("0")))
            payments_by_method[payment.method] = (count + 1, total + payment.amount)

        program = await self.program_repo.count_by_trainer_created_between(start, end)
        consultation = await self.consultation_repo.count_by_trainer_created_between(start, end)
        feedback = await self.feedback_repo.count_by_trainer_created_between(start, end)

        return AdminOverviewStatsDTO(
            period=command.period,
            trainers_total=len(trainers),
            trainers_new=sum(1 for t in trainers if _in_range(t.created_at, start, end)),
            trainers_blocked=sum(1 for t in trainers if not t.is_active),
            trainers_with_subscription=len(active_trainer_ids),
            clients_total=len(clients),
            clients_new=sum(1 for c in clients if _in_range(c.created_at, start, end)),
            clients_blocked=sum(1 for c in clients if not c.is_active),
            recurring_active=len({r.client_id for r in recurring}),
            trainings_completed=bookings_count(BookingStatus.COMPLETED),
            trainings_cancelled=bookings_count(BookingStatus.CANCELLED),
            trainings_active=bookings_count(BookingStatus.PENDING, BookingStatus.CONFIRMED),
            requests_program=sum(program.values()),
            requests_consultation=sum(consultation.values()),
            requests_feedback=sum(feedback.values()),
            revenue_period=_sum_amount(paid_period),
            revenue_purchase=_sum_amount(
                [s for s in paid_period if s.source == SubscriptionSource.PURCHASE]
            ),
            revenue_cash=_sum_amount(
                [s for s in paid_period if s.source == SubscriptionSource.CASH]
            ),
            payments_count=len(paid_period),
            trials_count=len(trials_period),
            revenue_all_time=_sum_amount(paid),
            top_trainers=[
                TopTrainerDTO(trainer_id=tid, name=names.get(tid, "—"), completed=count)
                for tid, count in top
            ],
            payments_by_method=payments_by_method,
        )
