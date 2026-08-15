from typing import Protocol

from src.domain.entities.subscription_price_plan import SubscriptionPricePlan


class SubscriptionPricePlanRepository(Protocol):
    async def get_active_plans(self) -> list[SubscriptionPricePlan]:
        ...

    async def get_by_id(self, price_plan_id: int) -> SubscriptionPricePlan | None:
        ...

    async def save(self, price_plan: SubscriptionPricePlan) -> SubscriptionPricePlan:
        ...