from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.stats.period import (
    ChartRange,
    StatsPeriod,
    chart_range,
    period_dates,
    period_datetimes,
)
from src.domain.constants import PROJECT_TIMEZONE
from src.domain.enums.booking import ACTIVE_BOOKING_STATUSES, BookingStatus
from src.domain.enums.subscription import PAID_SUBSCRIPTION_SOURCES, SubscriptionSource
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.bot_user import BotUserRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.utils import get_project_today

# «уснувший» — не заходил дольше этого срока, но бота не блокировал
DORMANT_AFTER_DAYS = 30


@dataclass(frozen=True)
class AdminChartSeriesDTO:
    range: ChartRange
    buckets: list[date]
    new_trainers: list[int]
    new_clients: list[int]
    new_guests: list[int]
    active_users: list[int]  # уникальные за день (за месяц — для «Всё время»)
    blocked_bot: list[int]
    revenue: list[Decimal]   # оплаченные подписки (онлайн + через админа), $
    trainings_completed: list[int]
    trainings_planned: list[int]
    trainings_cancelled: list[int]


@dataclass(frozen=True)
class AdminAnalyticsDTO:
    period: StatsPeriod
    # аудитория (все, кто писал боту)
    users_total: int
    trainers_total: int
    clients_total: int
    guests_total: int  # нажали /start, но не зарегистрировались
    # новые в периоде
    users_new: int
    trainers_new: int
    clients_new: int
    guests_new: int
    # активность
    active_period: int
    dau: int
    wau: int
    mau: int
    dormant: int  # не заходили > DORMANT_AFTER_DAYS, бот не блокировали
    # заблокировали бота (сейчас)
    blocked_total: int
    blocked_new: int  # заблокировали в периоде
    blocked_trainers: int
    blocked_clients: int
    # воронка тренеров
    trainers_trial: int       # получали пробный период
    trainers_paid: int        # хоть раз платили
    trainers_trial_to_paid: int
    trainers_on_trial_now: int
    series: AdminChartSeriesDTO


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _local_date(dt: datetime) -> date:
    return _aware(dt).astimezone(PROJECT_TIMEZONE).date()


def _in_range(dt: datetime | None, start: datetime, end: datetime) -> bool:
    return dt is not None and start <= _aware(dt) < end


@dataclass(frozen=True, eq=False)
class GetAdminAnalyticsRequest(UseCaseRequest):
    period: StatsPeriod = StatsPeriod.MONTH


@dataclass(kw_only=True)
class GetAdminAnalyticsUseCase(UseCase[GetAdminAnalyticsRequest, AdminAnalyticsDTO]):
    bot_user_repo: BotUserRepository
    trainer_repo: TrainerRepository
    client_repo: ClientRepository
    subscription_repo: TrainerSubscriptionRepository
    booking_repo: BookingRepository

    async def __call__(self, command: GetAdminAnalyticsRequest) -> AdminAnalyticsDTO:
        today = get_project_today()
        now = datetime.now(timezone.utc)
        date_from, _ = period_dates(command.period)
        start, end = period_datetimes(command.period)

        users = await self.bot_user_repo.get_all()
        trainer_tg = {t.tg_id for t in await self.trainer_repo.get_all()}
        client_tg = {
            c.tg_id for c in await self.client_repo.get_all() if c.has_telegram
        } - trainer_tg
        subscriptions = await self.subscription_repo.get_all()

        def role(tg_id: int) -> str:
            if tg_id in trainer_tg:
                return "trainer"
            return "client" if tg_id in client_tg else "guest"

        new_users = [u for u in users if _in_range(u.created_at, start, end)]
        blocked = [u for u in users if u.is_bot_blocked]
        dormant_border = now - timedelta(days=DORMANT_AFTER_DAYS)

        trial_ids = {s.trainer_id for s in subscriptions if s.source == SubscriptionSource.TRIAL}
        paid_ids = {s.trainer_id for s in subscriptions if s.source in PAID_SUBSCRIPTION_SOURCES}
        # «сейчас на триале» — действует только бесплатная подписка
        active_by_trainer: dict[int, set[SubscriptionSource]] = {}
        for s in subscriptions:
            if s.is_active(now):
                active_by_trainer.setdefault(s.trainer_id, set()).add(s.source)
        on_trial_now = sum(
            1 for sources in active_by_trainer.values() if sources == {SubscriptionSource.TRIAL}
        )

        # для «Всё время» ось графика начинается с месяца первого пользователя
        first_day = min((_local_date(u.created_at) for u in users), default=None)
        rng = chart_range(command.period, first_day)

        return AdminAnalyticsDTO(
            period=command.period,
            users_total=len(users),
            trainers_total=sum(1 for u in users if role(u.tg_id) == "trainer"),
            clients_total=sum(1 for u in users if role(u.tg_id) == "client"),
            guests_total=sum(1 for u in users if role(u.tg_id) == "guest"),
            users_new=len(new_users),
            trainers_new=sum(1 for u in new_users if role(u.tg_id) == "trainer"),
            clients_new=sum(1 for u in new_users if role(u.tg_id) == "client"),
            guests_new=sum(1 for u in new_users if role(u.tg_id) == "guest"),
            active_period=await self.bot_user_repo.count_active(date_from, today),
            dau=await self.bot_user_repo.count_active(today, today),
            wau=await self.bot_user_repo.count_active(today - timedelta(days=6), today),
            mau=await self.bot_user_repo.count_active(today - timedelta(days=29), today),
            dormant=sum(
                1 for u in users
                if not u.is_bot_blocked
                and _aware(u.last_activity_at or u.created_at) < dormant_border
            ),
            blocked_total=len(blocked),
            blocked_new=sum(1 for u in blocked if _in_range(u.blocked_at, start, end)),
            blocked_trainers=sum(1 for u in blocked if role(u.tg_id) == "trainer"),
            blocked_clients=sum(1 for u in blocked if role(u.tg_id) == "client"),
            trainers_trial=len(trial_ids),
            trainers_paid=len(paid_ids),
            trainers_trial_to_paid=len(trial_ids & paid_ids),
            trainers_on_trial_now=on_trial_now,
            series=await self._series(rng, users, role, subscriptions),
        )

    async def _series(self, rng: ChartRange, users, role, subscriptions) -> AdminChartSeriesDTO:
        buckets = rng.buckets()
        index = {bucket: i for i, bucket in enumerate(buckets)}
        size = len(buckets)
        new = {"trainer": [0] * size, "client": [0] * size, "guest": [0] * size}
        blocked_bot = [0] * size
        revenue = [Decimal("0")] * size
        completed, planned, cancelled = [0] * size, [0] * size, [0] * size

        def slot(day: date) -> int | None:
            return index[rng.bucket_of(day)] if rng.contains(day) else None

        for user in users:
            if (i := slot(_local_date(user.created_at))) is not None:
                new[role(user.tg_id)][i] += 1
            if user.blocked_at and (i := slot(_local_date(user.blocked_at))) is not None:
                blocked_bot[i] += 1

        for subscription in subscriptions:
            if subscription.source not in PAID_SUBSCRIPTION_SOURCES:
                continue
            if (i := slot(_local_date(subscription.created_at))) is not None:
                revenue[i] += subscription.amount

        for row in await self.booking_repo.get_stat_rows(rng.date_from, rng.date_to):
            i = index[rng.bucket_of(row.slot_date)]
            if row.status == BookingStatus.COMPLETED:
                completed[i] += 1
            elif row.status in ACTIVE_BOOKING_STATUSES:
                planned[i] += 1
            elif row.status == BookingStatus.CANCELLED:
                cancelled[i] += 1

        active = await self.bot_user_repo.count_active_by_bucket(
            rng.date_from, rng.date_to, by_month=rng.by_month
        )
        return AdminChartSeriesDTO(
            range=rng,
            buckets=buckets,
            new_trainers=new["trainer"],
            new_clients=new["client"],
            new_guests=new["guest"],
            active_users=[active.get(bucket, 0) for bucket in buckets],
            blocked_bot=blocked_bot,
            revenue=revenue,
            trainings_completed=completed,
            trainings_planned=planned,
            trainings_cancelled=cancelled,
        )
