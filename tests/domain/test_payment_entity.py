from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.domain.entities.payment import Payment
from src.domain.enums.payment import PaymentMethod, PaymentPurpose, PaymentStatus
from src.domain.exception.payment import PaymentStatusTransitionException


def make_payment(status: PaymentStatus = PaymentStatus.PENDING) -> Payment:
    return Payment(
        external_id="e1", trainer_id=1, method=PaymentMethod.MANUAL, amount=Decimal("30"),
        purpose=PaymentPurpose.SUBSCRIPTION, status=status,
    )


def test_pay_and_fail_are_final() -> None:
    payment = make_payment(PaymentStatus.WAITING_CONFIRMATION)
    payment.mark_paid(datetime.now(timezone.utc))
    assert payment.status == PaymentStatus.PAID and payment.is_final()
    with pytest.raises(PaymentStatusTransitionException):
        payment.mark_failed()

    failed = make_payment()
    failed.mark_failed()
    with pytest.raises(PaymentStatusTransitionException):
        failed.mark_paid(datetime.now(timezone.utc))


def test_default_currency_is_usd() -> None:
    assert make_payment().currency == "USD"


def test_method_labels() -> None:
    assert all(method.label() for method in PaymentMethod)
