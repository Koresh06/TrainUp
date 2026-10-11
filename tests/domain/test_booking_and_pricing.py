from datetime import time, timezone
from decimal import Decimal

import pytest

from src.domain.entities.booking import Booking
from src.domain.entities.trainer_pricing_rule import TrainerPricingRule
from src.domain.enums.booking import BookingStatus
from src.domain.exception.booking import BookingStatusTransitionException

START = time(10, 0, tzinfo=timezone.utc)


def make_booking(status: BookingStatus) -> Booking:
    return Booking(id=1, client_id=7, trainer_id=1, slot_id=1, status=status)


class TestBookingStatusTransitions:
    def test_confirm_pending(self) -> None:
        booking = make_booking(BookingStatus.PENDING)
        booking.confirm()
        assert booking.status == BookingStatus.CONFIRMED

    @pytest.mark.parametrize(
        "status",
        [BookingStatus.CONFIRMED, BookingStatus.CANCELLED, BookingStatus.COMPLETED],
    )
    def test_confirm_not_pending_raises(self, status: BookingStatus) -> None:
        # повторное «Подтвердить» в группе не должно воскрешать отменённую бронь
        with pytest.raises(BookingStatusTransitionException):
            make_booking(status).confirm()

    @pytest.mark.parametrize("status", [BookingStatus.PENDING, BookingStatus.CONFIRMED])
    def test_cancel_active(self, status: BookingStatus) -> None:
        booking = make_booking(status)
        booking.cancel()
        assert booking.status == BookingStatus.CANCELLED

    @pytest.mark.parametrize("status", [BookingStatus.CANCELLED, BookingStatus.COMPLETED])
    def test_cancel_inactive_raises(self, status: BookingStatus) -> None:
        with pytest.raises(BookingStatusTransitionException):
            make_booking(status).cancel()

    def test_complete_only_confirmed(self) -> None:
        with pytest.raises(BookingStatusTransitionException):
            make_booking(BookingStatus.PENDING).complete()


class TestPricingRule:
    def test_price_depends_on_boundary(self) -> None:
        rule = TrainerPricingRule(
            trainer_id=1,
            boundary_time=time(17, 0, tzinfo=timezone.utc),
            price_before=Decimal("20"),
            price_after=Decimal("30"),
        )
        assert rule.price_for(time(9, 0, tzinfo=timezone.utc)) == Decimal("20")
        assert rule.price_for(time(17, 0, tzinfo=timezone.utc)) == Decimal("30")

    def test_format_price_with_trainer_fee(self) -> None:
        rule = TrainerPricingRule(
            trainer_id=1,
            boundary_time=time(0, 0, tzinfo=timezone.utc),
            price_before=Decimal("0"),
            price_after=Decimal("25"),
            trainer_fee=Decimal("10"),
        )
        assert rule.format_price(START) == (
            "25 BYN + 10 BYN (работа тренера) = 35 BYN"
        )
