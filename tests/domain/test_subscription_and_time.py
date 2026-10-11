from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.subscription import SubscriptionPlan, SubscriptionStatus
from src.domain.utils import get_training_datetime_utc, is_slot_in_past

NOW = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)


def make_subscription(expired_at: datetime, status=SubscriptionStatus.ACTIVE) -> TrainerSubscription:
    return TrainerSubscription(
        trainer_id=1,
        plan=SubscriptionPlan.ONE_MONTH,
        amount=Decimal("30"),
        status=status,
        started_at=NOW - timedelta(days=30),
        expired_at=expired_at,
    )


class TestTrainerSubscription:
    def test_active_until_expiry(self) -> None:
        assert make_subscription(NOW + timedelta(minutes=1)).is_active(NOW)
        assert not make_subscription(NOW).is_active(NOW)

    def test_not_active_when_status_expired(self) -> None:
        subscription = make_subscription(NOW + timedelta(days=5), SubscriptionStatus.EXPIRED)
        assert not subscription.is_active(NOW)

    def test_is_active_default_now_handles_aware_datetimes(self) -> None:
        # регресс: раньше сравнивался naive datetime.now() с aware expired_at
        assert make_subscription(datetime.now(timezone.utc) + timedelta(hours=1)).is_active()


class TestSlotTime:
    def test_training_datetime_converted_from_project_timezone(self) -> None:
        # время слота хранится «как в Москве»: 10:00 MSK == 07:00 UTC
        slot = CalendarSlot(
            trainer_id=1,
            slot_date=date(2026, 10, 12),
            start_time=time(10, 0, tzinfo=timezone.utc),
            end_time=time(11, 0, tzinfo=timezone.utc),
        )
        assert get_training_datetime_utc(slot) == datetime(2026, 10, 12, 7, 0)

    def test_slot_in_past(self) -> None:
        past = CalendarSlot(
            trainer_id=1,
            slot_date=date(2020, 1, 1),
            start_time=time(10, 0),
            end_time=time(11, 0),
        )
        future = CalendarSlot(
            trainer_id=1,
            slot_date=date.today() + timedelta(days=2),
            start_time=time(10, 0),
            end_time=time(11, 0),
        )
        assert is_slot_in_past(past)
        assert not is_slot_in_past(future)
