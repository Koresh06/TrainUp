from dataclasses import dataclass

from src.domain.entities.subscription_price_plan import SubscriptionPricePlan
from src.domain.repositories.subscription_price_plan import (
    SubscriptionPricePlanRepository,
)
from src.application.use_cases.base import UseCase, UseCaseRequest


@dataclass(frozen=True, eq=False)
class GetActivePricePlansRequest(UseCaseRequest):
    pass


@dataclass(kw_only=True)
class GetActivePricePlansUseCase(
    UseCase[GetActivePricePlansRequest, list[SubscriptionPricePlan]]
):
    price_plan_repo: SubscriptionPricePlanRepository

    async def __call__(
        self, command: GetActivePricePlansRequest
    ) -> list[SubscriptionPricePlan]:
        return await self.price_plan_repo.get_active_plans()
