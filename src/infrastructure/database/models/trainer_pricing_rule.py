from datetime import time
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Integer, Numeric, Time

from src.domain.entities.trainer_pricing_rule import TrainerPricingRule


from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models import TrainerModel


class TrainerPricingRuleModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "trainer_pricing_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    boundary_time: Mapped[time] = mapped_column(Time(timezone=True))
    price_before: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    price_after: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    trainer: Mapped["TrainerModel"] = relationship(
        "TrainerModel",
        back_populates="pricing_rule",
    )

    @classmethod
    def from_entity(cls, entity: "TrainerPricingRule") -> "TrainerPricingRuleModel":
        return cls(
            trainer_id=entity.trainer_id,
            boundary_time=entity.boundary_time,
            price_before=entity.price_before,
            price_after=entity.price_after,
        )

    def to_entity(self) -> "TrainerPricingRule":
        return TrainerPricingRule(
            id=self.id,
            trainer_id=self.trainer_id,
            boundary_time=self.boundary_time,
            price_before=self.price_before,
            price_after=self.price_after,
        )

    def update_model(self, entity: "TrainerPricingRule") -> None:
        self.trainer_id = entity.trainer_id
        self.boundary_time = entity.boundary_time
        self.price_before = entity.price_before
        self.price_after = entity.price_after