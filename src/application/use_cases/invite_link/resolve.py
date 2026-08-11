from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.trainer_invite_link import TrainerInviteLink
from src.domain.exception.invite_link import TrainerInviteLinkInactiveException, TrainerInviteLinkNotFoundException
from src.domain.repositories.invite_link import TrainerInviteLinkRepository


@dataclass(frozen=True, eq=False)
class ResolveInviteLinkRequest(UseCaseRequest):
    token: str


@dataclass(kw_only=True)
class ResolveInviteLinkUseCase(UseCase[ResolveInviteLinkRequest, TrainerInviteLink]):
    invite_link_repo: TrainerInviteLinkRepository

    async def __call__(self, command: ResolveInviteLinkRequest) -> TrainerInviteLink:
        link = await self.invite_link_repo.get_by_token(command.token)
        if link is None:
            raise TrainerInviteLinkNotFoundException(token=command.token)
        if not link.is_active:
            raise TrainerInviteLinkInactiveException(token=command.token)
        return link