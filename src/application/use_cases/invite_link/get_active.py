from dataclasses import dataclass

from src.domain.entities.trainer_invite_link import TrainerInviteLink
from src.domain.exception.invite_link import TrainerInviteLinkNotFoundException
from src.domain.repositories.invite_link import TrainerInviteLinkRepository
from src.application.use_cases.base import UseCase, UseCaseRequest


@dataclass(frozen=True, eq=False)
class GetActiveInviteLinkRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class GetActiveInviteLinkUseCase(UseCase[GetActiveInviteLinkRequest, TrainerInviteLink]):
    invite_link_repo: TrainerInviteLinkRepository

    async def __call__(self, command: GetActiveInviteLinkRequest) -> TrainerInviteLink:
        link = await self.invite_link_repo.get_active_by_trainer_id(command.trainer_id)
        if link is None:
            raise TrainerInviteLinkNotFoundException(invite_link_id=None)
        return link