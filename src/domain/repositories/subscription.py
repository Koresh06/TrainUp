from typing import Protocol

from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.subscription import SubscriptionStatus


class TrainerSubscriptionRepository(Protocol):
    async def get_active_by_trainer_id(self, trainer_id: int) -> TrainerSubscription | None:
        ...

    async def get_by_id(self, subscription_id: int) -> TrainerSubscription | None:
        ...

    async def save(self, subscription: TrainerSubscription) -> TrainerSubscription:
        ...

    async def get_by_trainer_id(self, trainer_id: int) -> list[TrainerSubscription]:
        ...

    async def get_all_by_status(
        self, status: SubscriptionStatus
    ) -> list[TrainerSubscription]:
        ...

    async def get_all(self) -> list[TrainerSubscription]:
        ...
