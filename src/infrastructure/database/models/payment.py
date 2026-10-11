from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    VARCHAR,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    Numeric,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.entities.payment import Payment
from src.domain.enums.payment import PaymentMethod, PaymentPurpose, PaymentStatus

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin


class PaymentModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(VARCHAR(64), unique=True, index=True)
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="CASCADE"), index=True
    )
    method: Mapped[PaymentMethod] = mapped_column(SqlEnum(PaymentMethod))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(VARCHAR(8))
    status: Mapped[PaymentStatus] = mapped_column(SqlEnum(PaymentStatus), index=True)
    purpose: Mapped[PaymentPurpose] = mapped_column(SqlEnum(PaymentPurpose))
    purpose_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @classmethod
    def from_entity(cls, entity: Payment) -> "PaymentModel":
        return cls(
            external_id=entity.external_id,
            trainer_id=entity.trainer_id,
            method=entity.method,
            amount=entity.amount,
            currency=entity.currency,
            status=entity.status,
            purpose=entity.purpose,
            purpose_id=entity.purpose_id,
            description=entity.description,
            meta=entity.meta,
            paid_at=entity.paid_at,
        )

    def to_entity(self) -> Payment:
        return Payment(
            id=self.id,
            external_id=self.external_id,
            trainer_id=self.trainer_id,
            method=self.method,
            amount=self.amount,
            currency=self.currency,
            status=self.status,
            purpose=self.purpose,
            purpose_id=self.purpose_id,
            description=self.description,
            meta=dict(self.meta or {}),
            paid_at=self.paid_at,
            created_at=self.created_at,
        )

    def update_model(self, entity: Payment) -> None:
        self.status = entity.status
        self.meta = entity.meta
        self.paid_at = entity.paid_at
        self.description = entity.description
