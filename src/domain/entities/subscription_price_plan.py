from dataclasses import dataclass
from decimal import Decimal

from src.domain.entities.base import Entity
from src.domain.enums.subscription import SubscriptionPlan


@dataclass(kw_only=True)
class SubscriptionPricePlan(Entity):
    plan: SubscriptionPlan
    months: int
    price: Decimal
    is_active: bool = True