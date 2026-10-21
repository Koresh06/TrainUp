import logging
from dataclasses import dataclass
from decimal import Decimal

from src.application.interfaces.notification_service import (
    NotificationService,
    SubscriptionEvent,
    SubscriptionNotificationDTO,
)
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.subscription._shared import _activate_subscription
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.application.services.trainer_referral_reward import TrainerReferralRewardService
from src.domain.enums.subscription import (
    PAID_SUBSCRIPTION_SOURCES,
    SubscriptionPlan,
    SubscriptionSource,
)
from src.domain.exception.subscription import SubscriptionPricePlanNotFoundException
from src.domain.exception.trainer import TrainerNotFoundException
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.subscription_price_plan import SubscriptionPricePlanRepository
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class GrantSubscriptionRequest(UseCaseRequest):
    """Админ выдаёт подписку: по тарифу (оплата наличными/переводом) или на
    произвольное число дней (пробный/тестовый период)."""

    trainer_id: int
    source: SubscriptionSource
    price_plan_id: int | None = None
    days: int | None = None
    amount: Decimal | None = None  # None — для тарифа берём его цену, для дней — 0


@dataclass(kw_only=True)
class GrantSubscriptionUseCase(UseCase[GrantSubscriptionRequest, TrainerSubscription]):
    trainer_repo: TrainerRepository
    subscription_repo: TrainerSubscriptionRepository
    price_plan_repo: SubscriptionPricePlanRepository
    notification_service: NotificationService
    referral_reward: TrainerReferralRewardService
    transaction_manager: TransactionManager

    async def __call__(self, command: GrantSubscriptionRequest) -> TrainerSubscription:
        if (command.price_plan_id is None) == (command.days is None):
            raise ValueError("Specify either price_plan_id or days")

        trainer = await self.trainer_repo.get_by_id(command.trainer_id)
        if trainer is None:
            raise TrainerNotFoundException(trainer_id=command.trainer_id)

        if command.price_plan_id is not None:
            price_plan = await self.price_plan_repo.get_by_id(command.price_plan_id)
            if price_plan is None:
                raise SubscriptionPricePlanNotFoundException(command.price_plan_id)
            saved = await _activate_subscription(
                subscription_repo=self.subscription_repo,
                trainer_id=trainer.id,
                plan=price_plan.plan,
                amount=command.amount if command.amount is not None else price_plan.price,
                source=command.source,
                months=price_plan.months,
            )
        else:
            saved = await _activate_subscription(
                subscription_repo=self.subscription_repo,
                trainer_id=trainer.id,
                plan=SubscriptionPlan.CUSTOM,
                amount=command.amount or Decimal("0"),
                source=command.source,
                days=command.days,
            )
        expired_at = saved.expired_at
        if command.source in PAID_SUBSCRIPTION_SOURCES:
            # оплата наличными через админа — тоже первая оплата для рефералки
            await self.referral_reward.on_paid(trainer.id)
        await self.transaction_manager.commit()

        await self.notification_service.notify_subscription(
            SubscriptionNotificationDTO(
                chat_id=trainer.tg_id,
                event=SubscriptionEvent.GRANTED,
                expired_at=expired_at,
            )
        )
        logger.info(
            "[GrantSubscription:done] trainer_id=%s source=%s expired_at=%s",
            trainer.id, command.source, expired_at,
        )
        return saved
