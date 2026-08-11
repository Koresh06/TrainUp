from dataclasses import dataclass

from src.domain.entities.base import Entity


@dataclass(kw_only=True)
class TrainerInviteLink(Entity):
    trainer_id: int
    token: str
    is_active: bool