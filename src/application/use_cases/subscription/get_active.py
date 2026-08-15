from dataclasses import dataclass

from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.application.use_cases.base import UseCase, UseCaseRequest


@dataclass(frozen=True, eq=False)
class GetActiveSubscriptionRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class GetActiveSubscriptionUseCase(
    UseCase[GetActiveSubscriptionRequest, TrainerSubscription | None]
):
    subscription_repo: TrainerSubscriptionRepository

    async def __call__(
        self, command: GetActiveSubscriptionRequest
    ) -> TrainerSubscription | None:
        return await self.subscription_repo.get_active_by_trainer_id(command.trainer_id)
