"""Пробный период при регистрации, уведомления о его окончании и помощники
статистики (отрезки графиков, выгода тарифов)."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.application.use_cases.stats.period import StatsPeriod, chart_range
from src.application.use_cases.subscription.check_expiring import (
    CheckExpiringSubscriptionsRequest,
    CheckExpiringSubscriptionsUseCase,
)
from src.application.use_cases.trainer.register import (
    RegisterTrainerRequest,
    RegisterTrainerUseCase,
)
from src.domain.entities.subscription_price_plan import SubscriptionPricePlan
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.subscription import (
    SubscriptionPlan,
    SubscriptionSource,
    SubscriptionStatus,
)
from src.domain.utils import get_project_today
from src.presentation.telegram.features.trainer.register.texts import (
    cheapest_per_day,
    monthly_base_price,
    plan_button_label,
)
from tests.fakes.booking import FakeTransactionManager
from tests.fakes.common import (
    FakeSubscriptions,
    FakeTrainers,
    RecordingNotifications,
    _IdRepo,
)


def register_use_case(subs: FakeSubscriptions, trial_days: int) -> RegisterTrainerUseCase:
    return RegisterTrainerUseCase(
        trainer_repo=FakeTrainers(),
        invite_link_repo=_IdRepo(),
        booking_settings_repo=_IdRepo(),
        question_repo=_IdRepo(),
        subscription_repo=subs,
        transaction_manager=FakeTransactionManager(),
        trial_days=trial_days,
    )


REQUEST = RegisterTrainerRequest(tg_id=1, name="Иван", bio="", notification_chat_id=-1)


async def test_new_trainer_gets_free_trial() -> None:
    subs = FakeSubscriptions()
    trainer = await register_use_case(subs, trial_days=7)(REQUEST)

    trial = await subs.get_active_by_trainer_id(trainer.id)
    assert trial.source == SubscriptionSource.TRIAL and trial.amount == 0
    assert trial.plan == SubscriptionPlan.CUSTOM
    left = trial.expired_at - datetime.now(timezone.utc)
    assert timedelta(days=6, hours=23) < left <= timedelta(days=7)


async def test_trial_disabled_by_config() -> None:
    subs = FakeSubscriptions()
    trainer = await register_use_case(subs, trial_days=0)(REQUEST)
    assert await subs.get_active_by_trainer_id(trainer.id) is None


@pytest.mark.parametrize("source, is_trial", [
    (SubscriptionSource.TRIAL, True),
    (SubscriptionSource.PURCHASE, False),
])
async def test_expiry_notification_knows_about_trial(source, is_trial) -> None:
    from tests.application.test_subscription_use_cases import trainer

    now = datetime.now(timezone.utc)
    subs = FakeSubscriptions([
        TrainerSubscription(
            trainer_id=1, plan=SubscriptionPlan.CUSTOM, amount=Decimal("0"),
            status=SubscriptionStatus.ACTIVE, started_at=now, expired_at=now + timedelta(hours=2),
            source=source,
        )
    ])
    notifications = RecordingNotifications()
    await CheckExpiringSubscriptionsUseCase(
        subscription_repo=subs,
        trainer_repo=FakeTrainers([trainer(1)]),
        notification_service=notifications,
        transaction_manager=FakeTransactionManager(),
    )(CheckExpiringSubscriptionsRequest())

    [event] = notifications.of("notify_subscription")
    assert event.is_trial is is_trial


class TestChartRange:
    def test_today_shows_last_two_weeks(self) -> None:
        rng = chart_range(StatsPeriod.TODAY)
        buckets = rng.buckets()
        assert len(buckets) == 14 and buckets[-1] == get_project_today()

    def test_week_is_monday_to_sunday(self) -> None:
        buckets = chart_range(StatsPeriod.WEEK).buckets()
        assert len(buckets) == 7 and buckets[0].weekday() == 0
        assert get_project_today() in buckets

    def test_month_covers_all_days(self) -> None:
        rng = chart_range(StatsPeriod.MONTH)
        buckets = rng.buckets()
        assert buckets[0].day == 1 and (buckets[-1] + timedelta(days=1)).day == 1

    def test_all_time_monthly_with_minimum_and_cap(self) -> None:
        today = get_project_today()
        fresh = chart_range(StatsPeriod.ALL, today).buckets()
        assert len(fresh) == 6 and all(d.day == 1 for d in fresh)
        old = chart_range(StatsPeriod.ALL, date(2000, 1, 1)).buckets()
        assert len(old) == 24 and old[-1] == today.replace(day=1)

    def test_bucket_of_month(self) -> None:
        rng = chart_range(StatsPeriod.ALL)
        assert rng.bucket_of(date(2026, 5, 17)) == date(2026, 5, 1)


def plan(kind: SubscriptionPlan, months: int, price: str) -> SubscriptionPricePlan:
    return SubscriptionPricePlan(plan=kind, months=months, price=Decimal(price))


def test_plan_labels_show_monthly_price_and_saving() -> None:
    plans = [
        plan(SubscriptionPlan.ONE_MONTH, 1, "30"),
        plan(SubscriptionPlan.SIX_MONTHS, 6, "150"),
        plan(SubscriptionPlan.TWELVE_MONTHS, 12, "280"),
    ]
    base = monthly_base_price(plans)
    assert plan_button_label(plans[0], base) == "1 месяц — $30"
    assert plan_button_label(plans[1], base) == "6 месяцев — $150 · $25/мес · −17%"
    assert plan_button_label(plans[2], base) == "12 месяцев — $280 · $23.33/мес · −22%"
    assert cheapest_per_day(plans) == "$0.78"
