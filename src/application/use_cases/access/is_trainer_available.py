from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.trainer import TrainerRepository


@dataclass(frozen=True, eq=False)
class IsTrainerAvailableRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class IsTrainerAvailableUseCase(UseCase[IsTrainerAvailableRequest, bool]):
    """Тренер принимает клиентов: не заблокирован админом и подписка действует."""

    trainer_repo: TrainerRepository
    subscription_repo: TrainerSubscriptionRepository

    async def __call__(self, command: IsTrainerAvailableRequest) -> bool:
        trainer = await self.trainer_repo.get_by_id(command.trainer_id)
        if trainer is None or not trainer.is_active:
            return False
        return await self.subscription_repo.get_active_by_trainer_id(trainer.id) is not None
