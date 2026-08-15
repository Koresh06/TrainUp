from typing import Protocol

from src.domain.entities.trainer_subscription import TrainerSubscription


class TrainerSubscriptionRepository(Protocol):
    async def get_active_by_trainer_id(self, trainer_id: int) -> TrainerSubscription | None:
        ...

    async def get_by_id(self, subscription_id: int) -> TrainerSubscription | None:
        ...

    async def save(self, subscription: TrainerSubscription) -> TrainerSubscription:
        ...