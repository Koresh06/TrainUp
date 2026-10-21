from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.application.services.trainer_referral_reward import TrainerReferralRewardService
from src.application.interfaces.notification_service import SubscriptionEvent
from src.application.use_cases.subscription.check_expiring import (
    CheckExpiringSubscriptionsRequest,
    CheckExpiringSubscriptionsUseCase,
)
from src.application.use_cases.subscription.grant import (
    GrantSubscriptionRequest,
    GrantSubscriptionUseCase,
)
from src.domain.entities.subscription_price_plan import SubscriptionPricePlan
from src.domain.entities.trainer import Trainer
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.subscription import (
    SubscriptionPlan,
    SubscriptionSource,
    SubscriptionStatus,
)
from tests.fakes.booking import FakeTransactionManager
from tests.fakes.common import (
    FakePricePlans,
    FakeSubscriptions,
    FakeTrainers,
    RecordingNotifications,
)


def trainer(trainer_id: int = 1) -> Trainer:
    return Trainer(
        id=trainer_id, tg_id=100 + trainer_id, name="T", bio="", notification_chat_id=-1,
        is_active=True,
    )


def subscription(expires_in: timedelta, **kwargs) -> TrainerSubscription:
    now = datetime.now(timezone.utc)
    return TrainerSubscription(
        trainer_id=kwargs.pop("trainer_id", 1),
        plan=SubscriptionPlan.ONE_MONTH,
        amount=Decimal("30"),
        status=SubscriptionStatus.ACTIVE,
        started_at=now - timedelta(days=30),
        expired_at=now + expires_in,
        **kwargs,
    )


class TestGrantSubscription:
    @pytest.fixture
    def subs(self) -> FakeSubscriptions:
        return FakeSubscriptions()

    @pytest.fixture
    def notifications(self) -> RecordingNotifications:
        return RecordingNotifications()

    @pytest.fixture
    def use_case(self, subs, notifications) -> GrantSubscriptionUseCase:
        return GrantSubscriptionUseCase(
            trainer_repo=FakeTrainers([trainer()]),
            subscription_repo=subs,
            price_plan_repo=FakePricePlans(
                [SubscriptionPricePlan(id=5, plan=SubscriptionPlan.THREE_MONTHS, months=3, price=Decimal("80"))]
            ),
            notification_service=notifications,
            referral_reward=TrainerReferralRewardService(
                trainer_repo=FakeTrainers([trainer()]),
                subscription_repo=subs,
                notification_service=notifications,
            ),
            transaction_manager=FakeTransactionManager(),
        )

    async def test_trial_days_extend_current_subscription(self, use_case, subs, notifications) -> None:
        current = await subs.save(subscription(timedelta(days=10)))

        granted = await use_case(
            GrantSubscriptionRequest(trainer_id=1, source=SubscriptionSource.TRIAL, days=7)
        )

        assert granted.plan == SubscriptionPlan.CUSTOM
        assert granted.amount == Decimal("0")
        assert granted.expired_at == current.expired_at + timedelta(days=7)
        assert notifications.of("notify_subscription")[0].event == SubscriptionEvent.GRANTED

    async def test_cash_by_plan_takes_plan_price(self, use_case) -> None:
        granted = await use_case(
            GrantSubscriptionRequest(trainer_id=1, source=SubscriptionSource.CASH, price_plan_id=5)
        )
        assert granted.source == SubscriptionSource.CASH
        assert granted.amount == Decimal("80")
        assert granted.plan == SubscriptionPlan.THREE_MONTHS

    async def test_requires_exactly_one_of_plan_or_days(self, use_case) -> None:
        with pytest.raises(ValueError):
            await use_case(
                GrantSubscriptionRequest(trainer_id=1, source=SubscriptionSource.TRIAL)
            )


class TestCheckExpiringSubscriptions:
    def make(self, subs: FakeSubscriptions, notifications: RecordingNotifications):
        return CheckExpiringSubscriptionsUseCase(
            subscription_repo=subs,
            trainer_repo=FakeTrainers([trainer(1), trainer(2)]),
            notification_service=notifications,
            transaction_manager=FakeTransactionManager(),
        )

    async def test_warning_sent_once_per_threshold(self) -> None:
        subs, notifications = FakeSubscriptions(), RecordingNotifications()
        sub = await subs.save(subscription(timedelta(hours=40)))
        use_case = self.make(subs, notifications)

        await use_case(CheckExpiringSubscriptionsRequest())
        await use_case(CheckExpiringSubscriptionsRequest())  # повторный прогон крона

        events = notifications.of("notify_subscription")
        assert [e.event for e in events] == [SubscriptionEvent.WARNING]
        assert sub.notified_stage == 1

        sub.expired_at = datetime.now(timezone.utc) + timedelta(hours=2)
        await use_case(CheckExpiringSubscriptionsRequest())
        assert len(notifications.of("notify_subscription")) == 2
        assert sub.notified_stage == 2

    async def test_far_expiry_no_warning(self) -> None:
        subs, notifications = FakeSubscriptions(), RecordingNotifications()
        await subs.save(subscription(timedelta(days=10)))
        await self.make(subs, notifications)(CheckExpiringSubscriptionsRequest())
        assert notifications.calls == []

    async def test_expired_marked_and_trainer_notified(self) -> None:
        subs, notifications = FakeSubscriptions(), RecordingNotifications()
        sub = await subs.save(subscription(timedelta(minutes=-5)))

        await self.make(subs, notifications)(CheckExpiringSubscriptionsRequest())

        assert sub.status == SubscriptionStatus.EXPIRED
        [event] = notifications.of("notify_subscription")
        assert event.event == SubscriptionEvent.EXPIRED
        assert event.chat_id == 101

    async def test_superseded_subscription_expires_silently(self) -> None:
        # продлили заранее: старая истекла, новая действует — тренера не беспокоим
        subs, notifications = FakeSubscriptions(), RecordingNotifications()
        old = await subs.save(subscription(timedelta(minutes=-5)))
        await subs.save(subscription(timedelta(days=30)))

        await self.make(subs, notifications)(CheckExpiringSubscriptionsRequest())

        assert old.status == SubscriptionStatus.EXPIRED
        assert notifications.calls == []

    @pytest.mark.parametrize(
        "hours_left, stage", [(100, 0), (48, 1), (10, 1), (3, 2), (0.5, 2)]
    )
    def test_warning_stage(self, hours_left: float, stage: int) -> None:
        assert CheckExpiringSubscriptionsUseCase._warning_stage(timedelta(hours=hours_left)) == stage
