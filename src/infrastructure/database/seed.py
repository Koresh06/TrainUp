import logging

from decimal import Decimal

from src.domain.entities.subscription_price_plan import SubscriptionPricePlan
from src.domain.enums.subscription import SubscriptionPlan
from src.domain.repositories.subscription_price_plan import (
    SubscriptionPricePlanRepository,
)
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


DEFAULT_SUBSCRIPTION_PRICE_PLANS: list[tuple[SubscriptionPlan, int, Decimal]] = [
    (SubscriptionPlan.ONE_MONTH, 1, Decimal("30")),
    (SubscriptionPlan.THREE_MONTHS, 3, Decimal("80")),
    (SubscriptionPlan.SIX_MONTHS, 6, Decimal("150")),
    (SubscriptionPlan.TWELVE_MONTHS, 12, Decimal("280")),
]


async def seed_subscription_price_plans(container) -> None:
    async with container() as request_container:
        repo: SubscriptionPricePlanRepository = await request_container.get(
            SubscriptionPricePlanRepository
        )
        transaction_manager: TransactionManager = await request_container.get(
            TransactionManager
        )

        existing = await repo.get_all()
        if existing:
            logger.info(
                "[SeedSubscriptionPricePlans] skip — %s plans already exist",
                len(existing),
            )
            return

        for plan, months, price in DEFAULT_SUBSCRIPTION_PRICE_PLANS:
            await repo.save(
                SubscriptionPricePlan(
                    plan=plan,
                    months=months,
                    price=price,
                    is_active=True,
                )
            )
        await transaction_manager.commit()

        logger.info(
            "[SeedSubscriptionPricePlans] created %s default plans",
            len(DEFAULT_SUBSCRIPTION_PRICE_PLANS),
        )
