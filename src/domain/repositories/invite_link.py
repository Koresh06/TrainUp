from typing import Protocol

from src.domain.entities.invite_link import TrainerInviteLink


class TrainerInviteLinkRepository(Protocol):
    async def get_by_token(self, token: str) -> TrainerInviteLink | None:
        ...

    async def get_active_by_trainer_id(self, trainer_id: int) -> TrainerInviteLink | None:
        ...

    async def save(self, invite_link: TrainerInviteLink) -> None:
        ...