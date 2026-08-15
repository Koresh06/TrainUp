import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.subscription import SubscriptionStatus
from src.domain.exception.subscription import SubscriptionPricePlanNotFoundException
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.subscription_price_plan import SubscriptionPricePlanRepository
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.infrastructure.database.transaction_manager.base import TransactionManager


logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class PurchaseSubscriptionRequest(UseCaseRequest):
    trainer_id: int
    price_plan_id: int


@dataclass(kw_only=True)
class PurchaseSubscriptionUseCase(UseCase[PurchaseSubscriptionRequest, TrainerSubscription]):
    price_plan_repo: SubscriptionPricePlanRepository
    subscription_repo: TrainerSubscriptionRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: PurchaseSubscriptionRequest) -> TrainerSubscription:
        price_plan = await self.price_plan_repo.get_by_id(command.price_plan_id)
        if price_plan is None:
            raise SubscriptionPricePlanNotFoundException(command.price_plan_id)

        now = datetime.now(timezone.utc)
        current = await self.subscription_repo.get_active_by_trainer_id(command.trainer_id)

        # если текущая активная подписка ещё не истекла — продлеваем от её конца,
        # иначе (нет подписки или уже истекла) — считаем от текущего момента
        base_start = current.expired_at if current is not None and current.expired_at > now else now
        expired_at = base_start + relativedelta(months=price_plan.months)

        subscription = TrainerSubscription(
            trainer_id=command.trainer_id,
            plan=price_plan.plan,
            amount=price_plan.price,
            status=SubscriptionStatus.ACTIVE,
            started_at=now,
            expired_at=expired_at,
        )
        saved = await self.subscription_repo.save(subscription)
        await self.transaction_manager.commit()

        logger.info(
            "[PurchaseSubscription:done] trainer_id=%s plan=%s expired_at=%s",
            command.trainer_id, price_plan.plan, expired_at,
        )
        return saved