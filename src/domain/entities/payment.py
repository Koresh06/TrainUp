from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from src.domain.entities.base import Entity
from src.domain.enums.payment import (
    PAYMENT_BASE_CURRENCY,
    PaymentMethod,
    PaymentPurpose,
    PaymentStatus,
)
from src.domain.exception.payment import PaymentStatusTransitionException


@dataclass(kw_only=True)
class Payment(Entity):
    external_id: str           # наш id платежа: payload инвойса / metadata ЮKassa
    trainer_id: int
    method: PaymentMethod
    amount: Decimal            # в PAYMENT_BASE_CURRENCY (USD)
    purpose: PaymentPurpose
    purpose_id: int | None = None
    currency: str = PAYMENT_BASE_CURRENCY
    status: PaymentStatus = PaymentStatus.PENDING
    description: str | None = None
    meta: dict = field(default_factory=dict)  # данные провайдера: ссылка, сумма в RUB/XTR…
    paid_at: datetime | None = None

    def is_final(self) -> bool:
        return self.status in (PaymentStatus.PAID, PaymentStatus.FAILED)

    def mark_paid(self, now: datetime) -> None:
        if self.is_final():
            raise PaymentStatusTransitionException(
                external_id=self.external_id, status=self.status
            )
        self.status = PaymentStatus.PAID
        self.paid_at = now
        self.touch()

    def mark_failed(self) -> None:
        if self.is_final():
            raise PaymentStatusTransitionException(
                external_id=self.external_id, status=self.status
            )
        self.status = PaymentStatus.FAILED
        self.touch()
