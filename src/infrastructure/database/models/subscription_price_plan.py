from decimal import Decimal

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Boolean, Enum as SqlEnum, Numeric

from src.domain.entities.subscription_price_plan import SubscriptionPricePlan
from src.domain.enums.subscription import SubscriptionPlan

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin


class SubscriptionPricePlanModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "subscription_price_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan: Mapped[SubscriptionPlan] = mapped_column(
        SqlEnum(SubscriptionPlan), unique=True
    )
    months: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    @classmethod
    def from_entity(cls, entity: SubscriptionPricePlan) -> "SubscriptionPricePlanModel":
        return cls(
            plan=entity.plan,
            months=entity.months,
            price=entity.price,
            is_active=entity.is_active,
        )

    def to_entity(self) -> "SubscriptionPricePlan":
        return SubscriptionPricePlan(
            id=self.id,
            plan=self.plan,
            months=self.months,
            price=self.price,
            is_active=self.is_active,
        )

    def update_model(self, entity: "SubscriptionPricePlan") -> None:
        self.plan = entity.plan
        self.months = entity.months
        self.price = entity.price
        self.is_active = entity.is_active
