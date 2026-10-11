from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from src.domain.entities.base import Entity
from src.domain.enums.subscription import (
    SubscriptionPlan,
    SubscriptionSource,
    SubscriptionStatus,
)


@dataclass(kw_only=True)
class TrainerSubscription(Entity):
    trainer_id: int
    plan: SubscriptionPlan
    amount: Decimal
    status: SubscriptionStatus
    started_at: datetime
    expired_at: datetime
    source: SubscriptionSource = SubscriptionSource.PURCHASE
    # сколько уведомлений об окончании уже отправлено тренеру:
    # 0..len(SUBSCRIPTION_WARNING_HOURS) — предупреждения, +1 — «подписка истекла»
    notified_stage: int = 0

    def is_active(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        return self.status == SubscriptionStatus.ACTIVE and self.expired_at > now

    def expired(self) -> None:
        self.status = SubscriptionStatus.EXPIRED
        self.touch()

    def cancel(self) -> None:
        self.status = SubscriptionStatus.CANCELLED
        self.touch()
