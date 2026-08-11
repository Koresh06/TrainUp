from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from src.domain.entities.base import Entity
from src.domain.enums.subscription import SubscriptionPlan, SubscriptionStatus


@dataclass(kw_only=True)
class TrainerSubscription(Entity):
    trainer_id: int
    plan: SubscriptionPlan
    amount: Decimal
    status: SubscriptionStatus
    started_at: datetime
    expired_at: datetime

    def is_active(self) -> bool:
        if self.status == SubscriptionStatus.ACTIVE and self.expired_at > datetime.now():
            return True
        return False
    
    def expired(self) -> None:
        self.status = SubscriptionStatus.EXPIRED
        self.touch()

    def cancel(self) -> None:
        self.status = SubscriptionStatus.CANCELLED
        self.touch()