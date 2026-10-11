from datetime import datetime, timedelta, timezone
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.subscription import (
    SubscriptionPlan,
    SubscriptionSource,
    SubscriptionStatus,
)
from src.domain.repositories.subscription import TrainerSubscriptionRepository


async def _activate_subscription(
    *,
    subscription_repo: TrainerSubscriptionRepository,
    trainer_id: int,
    plan: SubscriptionPlan,
    amount: Decimal,
    source: SubscriptionSource,
    months: int | None = None,
    days: int | None = None,
) -> TrainerSubscription:
    """Новая подписка; если текущая ещё действует — срок добавляется к её концу.
    Общая для выдачи админом и подтверждения оплаты. Commit — на вызывающем."""
    now = datetime.now(timezone.utc)
    current = await subscription_repo.get_active_by_trainer_id(trainer_id)
    base_start = current.expired_at if current is not None and current.expired_at > now else now
    if months is not None:
        expired_at = base_start + relativedelta(months=months)
    else:
        expired_at = base_start + timedelta(days=days or 0)

    return await subscription_repo.save(
        TrainerSubscription(
            trainer_id=trainer_id,
            plan=plan,
            amount=amount,
            status=SubscriptionStatus.ACTIVE,
            started_at=now,
            expired_at=expired_at,
            source=source,
        )
    )
