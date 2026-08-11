from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    DateTime,
    ForeignKey,
    BigInteger,
    Integer,
    VARCHAR,
    Boolean,
    Enum as SqlEnum,
    Numeric,
)

from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.subscription import SubscriptionPlan, SubscriptionStatus

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin


if TYPE_CHECKING:
    from src.infrastructure.database.models import TrainerModel


class TrainerSubscriptionModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "trainer_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="CASCADE"),
        index=True,
    )
    plan: Mapped[SubscriptionPlan] = mapped_column(SqlEnum(SubscriptionPlan))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[SubscriptionStatus] = mapped_column(
        SqlEnum(SubscriptionStatus),
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    trainer: Mapped["TrainerModel"] = relationship(
        "TrainerModel",
        back_populates="subscriptions",
    )

    @classmethod
    def from_entity(cls, entity: "TrainerSubscription") -> "TrainerSubscriptionModel":
        return cls(
            trainer_id=entity.trainer_id,
            plan=entity.plan,
            amount=entity.amount,
            status=entity.status,
            started_at=entity.started_at,
            expired_at=entity.expired_at,
        )

    def to_entity(self) -> "TrainerSubscription":
        return TrainerSubscription(
            id=self.id,
            trainer_id=self.trainer_id,
            plan=self.plan,
            amount=self.amount,
            status=self.status,
            started_at=self.started_at,
            expired_at=self.expired_at,
        )

    def update_model(self, entity: "TrainerSubscription") -> None:
        self.trainer_id = entity.trainer_id
        self.plan = entity.plan
        self.amount = entity.amount
        self.status = entity.status
        self.started_at = entity.started_at
        self.expired_at = entity.expired_at
