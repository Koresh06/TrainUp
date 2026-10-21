from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.stats.period import (
    ChartRange,
    StatsPeriod,
    chart_range,
    period_dates,
    period_datetimes,
)
from src.domain.enums.booking import ACTIVE_BOOKING_STATUSES, BookingStatus
from src.domain.repositories.booking import BookingRepository, BookingStatRow
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.consultation import ConsultationRequestRepository
from src.domain.repositories.feedback import FeedbackRepository
from src.domain.repositories.program import ProgramRequestRepository
from src.domain.repositories.recurring_booking import RecurringBookingRepository
from src.domain.utils import get_project_today


@dataclass(frozen=True, eq=False)
class GetTrainerStatsRequest(UseCaseRequest):
    trainer_id: int
    period: StatsPeriod = StatsPeriod.MONTH


@dataclass(frozen=True)
class TopClientDTO:
    name: str
    completed: int


@dataclass(frozen=True)
class TrainerChartSeriesDTO:
    """Ряды для графиков тренера: по дням (или месяцам для «Всё время»)."""

    range: ChartRange
    buckets: list[date]
    completed: list[int]
    planned: list[int]
    cancelled: list[int]
    income: list[Decimal]
    # загрузка: [weekday 0..6][hour 0..23] — проведённые + запланированные
    load: list[list[int]]


@dataclass(frozen=True)
class TrainerStatsDTO:
    period: StatsPeriod
    # клиенты
    total_clients: int
    new_clients: int
    active_clients: int  # были хотя бы на одной тренировке в периоде
    recurring_clients: int
    # тренировки
    completed_trainings: int
    cancelled_bookings: int  # отменено в периоде (по дате отмены)
    planned_trainings: int   # активные записи с сегодняшнего дня до конца периода
    upcoming_bookings: int   # все будущие активные записи
    cancel_rate: float       # доля отменённых среди занятий периода (по дате занятия)
    # деньги (BYN, по цене, зафиксированной в записи)
    income: Decimal
    average_check: Decimal
    expected_income: Decimal  # по запланированным до конца периода
    # заявки клиентов, созданные в периоде
    requests_count: int
    # клиент не пришёл (отметил тренер)
    no_show_trainings: int = 0
    busiest_weekdays: list[int] = field(default_factory=list)
    busiest_hours: list[int] = field(default_factory=list)
    top_clients: list[TopClientDTO] = field(default_factory=list)
    series: TrainerChartSeriesDTO | None = None


def _in_range(dt: datetime, start: datetime, end: datetime) -> bool:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return start <= dt < end


def _top_keys(counter: Counter, limit: int) -> list[int]:
    """Самые частые значения; ничьи с лидером тоже попадают, но не больше limit."""
    if not counter:
        return []
    ranked = counter.most_common()
    best = ranked[0][1]
    return [key for key, count in ranked[:limit] if count >= best * 0.8]


@dataclass(kw_only=True)
class GetTrainerStatsUseCase(UseCase[GetTrainerStatsRequest, TrainerStatsDTO]):
    client_repo: ClientRepository
    booking_repo: BookingRepository
    recurring_repo: RecurringBookingRepository
    program_repo: ProgramRequestRepository
    consultation_repo: ConsultationRequestRepository
    feedback_repo: FeedbackRepository

    async def __call__(self, command: GetTrainerStatsRequest) -> TrainerStatsDTO:
        trainer_id = command.trainer_id
        today = get_project_today()
        date_from, _ = period_dates(command.period)
        start, end = period_datetimes(command.period)

        # строки берём сразу на весь график: он может выходить за период
        # (последние 14 дней для «Сегодня», будущие дни недели/месяца)
        preview = chart_range(command.period)
        rows = await self.booking_repo.get_stat_rows(
            min(date_from, preview.date_from), max(today, preview.date_to), trainer_id
        )
        first_day = min((r.slot_date for r in rows), default=None)
        rng = chart_range(command.period, first_day) if command.period == StatsPeriod.ALL else preview

        period_end = max(today, rng.date_to) if command.period != StatsPeriod.ALL else today
        in_period = [r for r in rows if date_from <= r.slot_date <= today]
        completed = [r for r in in_period if r.status == BookingStatus.COMPLETED]
        planned = [
            r for r in rows
            if r.status in ACTIVE_BOOKING_STATUSES and today <= r.slot_date <= period_end
        ]
        slot_cancelled = [r for r in in_period if r.status == BookingStatus.CANCELLED]
        considered = len(completed) + len(slot_cancelled) + sum(
            1 for r in in_period if r.status in ACTIVE_BOOKING_STATUSES
        )

        priced = [r.price for r in completed if r.price]
        income = sum(priced, Decimal("0"))

        clients = await self.client_repo.get_by_trainer_id(trainer_id)
        names = {
            c.id: " ".join(part for part in (c.first_name, c.last_name) if part)
            for c in clients
        }
        visits = Counter(r.client_id for r in completed)

        load_rows = [
            r for r in in_period
            if r.status in (BookingStatus.COMPLETED, *ACTIVE_BOOKING_STATUSES)
        ]

        requests_count = 0
        for repo in (self.program_repo, self.consultation_repo, self.feedback_repo):
            counts = await repo.count_by_trainer_created_between(start, end)
            requests_count += counts.get(trainer_id, 0)

        return TrainerStatsDTO(
            period=command.period,
            total_clients=len(clients),
            new_clients=sum(1 for c in clients if _in_range(c.created_at, start, end)),
            active_clients=len(visits),
            recurring_clients=len(
                {r.client_id for r in await self.recurring_repo.get_active_by_trainer_id(trainer_id)}
            ),
            completed_trainings=len(completed),
            cancelled_bookings=await self.booking_repo.count_cancelled_by_trainer_in_period(
                trainer_id, date_from, today
            ),
            planned_trainings=len(planned),
            upcoming_bookings=len(await self.booking_repo.get_upcoming_by_trainer(trainer_id)),
            cancel_rate=len(slot_cancelled) / considered if considered else 0.0,
            income=income,
            average_check=(income / len(priced)) if priced else Decimal("0"),
            expected_income=sum((r.price for r in planned if r.price), Decimal("0")),
            requests_count=requests_count,
            no_show_trainings=sum(1 for r in in_period if r.status == BookingStatus.NO_SHOW),
            busiest_weekdays=_top_keys(Counter(r.slot_date.weekday() for r in load_rows), 2),
            busiest_hours=_top_keys(Counter(r.start_time.hour for r in load_rows), 2),
            top_clients=[
                TopClientDTO(name=names.get(client_id, "—"), completed=count)
                for client_id, count in visits.most_common(3)
            ],
            series=self._series(rows, rng),
        )

    @staticmethod
    def _series(rows: list[BookingStatRow], rng: ChartRange) -> TrainerChartSeriesDTO:
        buckets = rng.buckets()
        index = {bucket: i for i, bucket in enumerate(buckets)}
        completed = [0] * len(buckets)
        planned = [0] * len(buckets)
        cancelled = [0] * len(buckets)
        income = [Decimal("0")] * len(buckets)
        load = [[0] * 24 for _ in range(7)]

        for row in rows:
            if not rng.contains(row.slot_date):
                continue
            i = index[rng.bucket_of(row.slot_date)]
            if row.status == BookingStatus.COMPLETED:
                completed[i] += 1
                income[i] += row.price or Decimal("0")
            elif row.status in ACTIVE_BOOKING_STATUSES:
                planned[i] += 1
            elif row.status == BookingStatus.CANCELLED:
                cancelled[i] += 1
                continue
            load[row.slot_date.weekday()][row.start_time.hour] += 1

        return TrainerChartSeriesDTO(
            range=rng,
            buckets=buckets,
            completed=completed,
            planned=planned,
            cancelled=cancelled,
            income=income,
            load=load,
        )
