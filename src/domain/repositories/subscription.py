from typing import Protocol

from src.domain.entities.trainer_subscription import TrainerSubscription


class TrainerSubscriptionRepository(Protocol):
    async def get_active_by_trainer_id(self, trainer_id: int) -> list:
        ...

    async def save(self, subscription: TrainerSubscription) -> TrainerSubscription:
        ...