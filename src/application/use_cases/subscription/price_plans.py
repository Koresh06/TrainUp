import logging
from dataclasses import dataclass
from decimal import Decimal

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.subscription_price_plan import SubscriptionPricePlan
from src.domain.exception.subscription import SubscriptionPricePlanNotFoundException
from src.domain.repositories.subscription_price_plan import (
    SubscriptionPricePlanRepository,
)
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class GetAllPricePlansRequest(UseCaseRequest):
    pass


@dataclass(kw_only=True)
class GetAllPricePlansUseCase(UseCase[GetAllPricePlansRequest, list[SubscriptionPricePlan]]):
    price_plan_repo: SubscriptionPricePlanRepository

    async def __call__(self, command: GetAllPricePlansRequest) -> list[SubscriptionPricePlan]:
        plans = await self.price_plan_repo.get_all()
        return sorted(plans, key=lambda p: p.months)


@dataclass(frozen=True, eq=False)
class UpdatePricePlanPriceRequest(UseCaseRequest):
    price_plan_id: int
    price: Decimal
    changed_by_tg_id: int


@dataclass(kw_only=True)
class UpdatePricePlanPriceUseCase(
    UseCase[UpdatePricePlanPriceRequest, SubscriptionPricePlan]
):
    """
    Новая цена действует для новых оплат. Уже созданный платёж хранит свою
    сумму (payments.amount), поэтому тренер, который открыл оплату до смены
    цены, заплатит то, что ему показали.
    """

    price_plan_repo: SubscriptionPricePlanRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: UpdatePricePlanPriceRequest) -> SubscriptionPricePlan:
        plan = await self.price_plan_repo.get_by_id(command.price_plan_id)
        if plan is None:
            raise SubscriptionPricePlanNotFoundException(command.price_plan_id)

        old_price = plan.price
        plan.price = command.price
        plan.touch()
        saved = await self.price_plan_repo.save(plan)
        await self.transaction_manager.commit()

        logger.info(
            "[UpdatePricePlanPrice:done] plan=%s %s -> %s by tg_id=%s",
            plan.plan.value, old_price, command.price, command.changed_by_tg_id,
        )
        return saved
