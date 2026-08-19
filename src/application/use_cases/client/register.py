from dataclasses import dataclass
import logging

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.client import Client
from src.domain.enums.training import SportExperience
from src.domain.repositories.client import ClientRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager


logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class RegisterClientRequest(UseCaseRequest):
    tg_id: int
    trainer_id: int
    first_name: str
    last_name: str | None
    username: str | None
    phone: str
    age: int
    sport_experience: str
    health_conditions: list[str]
    health_conditions_other: str | None
    goals: list[str]
    health_notes: str | None
    injuries: str | None


@dataclass(kw_only=True)
class RegisterClientUseCase(UseCase[RegisterClientRequest, Client]):
    client_repo: ClientRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: RegisterClientRequest) -> Client:
        logger.info("[RegisterClient] tg_id=%s trainer_id=%s", command.tg_id, command.trainer_id)

        existing = await self.client_repo.get_by_tg_id(command.tg_id)
        if existing is not None:
            # кидает AssigningClientToAnotherTrainerError, если клиент уже
            # привязан к ДРУГОМУ тренеру — регистрация по чужой ссылке не проходит
            existing.assingn_trainer(command.trainer_id)
            logger.info("[RegisterClient:already_registered] client_id=%s", existing.id)
            return existing

        client = Client(
            tg_id=command.tg_id,
            trainer_id=command.trainer_id,
            first_name=command.first_name,
            last_name=command.last_name,
            username=command.username,
            phone=command.phone,
            age=command.age,
            sport_experience=SportExperience(command.sport_experience),
            health_conditions=command.health_conditions,
            health_conditions_other=command.health_conditions_other,
            goals=command.goals,
            health_notes=command.health_notes,
            injuries=command.injuries,
        )
        saved = await self.client_repo.save(client)
        await self.transaction_manager.commit()

        logger.info("[RegisterClient:done] client_id=%s", saved.id)
        return saved