import logging
import secrets
from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.trainer_invite_link import TrainerInviteLink
from src.domain.repositories.invite_link import TrainerInviteLinkRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager


logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class CreateTrainerInviteLinkRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class CreateTrainerInviteLinkUseCase(UseCase[CreateTrainerInviteLinkRequest, TrainerInviteLink]):
    invite_link_repo: TrainerInviteLinkRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: CreateTrainerInviteLinkRequest) -> TrainerInviteLink:
        link = TrainerInviteLink(
            trainer_id=command.trainer_id,
            token=secrets.token_urlsafe(16),
            is_active=True,
        )
        saved = await self.invite_link_repo.save(link)
        await self.transaction_manager.commit()

        logger.info("[CreateTrainerInviteLink:done] trainer_id=%s", command.trainer_id)
        return saved