from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.repositories.subscription import TrainerSubscriptionRepository


@dataclass(frozen=True, eq=False)
class GetSubscriptionsByTrainerRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class GetSubscriptionsByTrainerUseCase(
    UseCase[GetSubscriptionsByTrainerRequest, list[TrainerSubscription]]
):
    subscription_repo: TrainerSubscriptionRepository

    async def __call__(
        self, command: GetSubscriptionsByTrainerRequest
    ) -> list[TrainerSubscription]:
        return await self.subscription_repo.get_by_trainer_id(command.trainer_id)
