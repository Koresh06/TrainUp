from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.client import Client
from src.domain.entities.trainer import Trainer
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.trainer import TrainerRepository


@dataclass(frozen=True)
class UserAccessDTO:
    trainer: Trainer | None
    trainer_subscription_active: bool
    client: Client | None
    # тренер клиента не заблокирован и у него действует подписка
    client_trainer_available: bool

    @property
    def is_blocked(self) -> bool:
        """Пользователь заблокирован администратором (как тренер или как клиент)."""
        return (self.trainer is not None and not self.trainer.is_active) or (
            self.client is not None and not self.client.is_active
        )


@dataclass(frozen=True, eq=False)
class GetUserAccessRequest(UseCaseRequest):
    tg_id: int


@dataclass(kw_only=True)
class GetUserAccessUseCase(UseCase[GetUserAccessRequest, UserAccessDTO]):
    """Единая проверка прав для middleware: блокировки админом и подписка тренера."""

    trainer_repo: TrainerRepository
    client_repo: ClientRepository
    subscription_repo: TrainerSubscriptionRepository

    async def __call__(self, command: GetUserAccessRequest) -> UserAccessDTO:
        trainer = await self.trainer_repo.get_by_tg_id(command.tg_id)
        trainer_subscription_active = (
            trainer is not None
            and await self.subscription_repo.get_active_by_trainer_id(trainer.id) is not None
        )

        client = await self.client_repo.get_by_tg_id(command.tg_id)
        client_trainer_available = False
        if client is not None:
            client_trainer = await self.trainer_repo.get_by_id(client.trainer_id)
            client_trainer_available = (
                client_trainer is not None
                and client_trainer.is_active
                and await self.subscription_repo.get_active_by_trainer_id(client_trainer.id)
                is not None
            )

        return UserAccessDTO(
            trainer=trainer,
            trainer_subscription_active=trainer_subscription_active,
            client=client,
            client_trainer_available=client_trainer_available,
        )
