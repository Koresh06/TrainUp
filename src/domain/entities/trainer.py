from dataclasses import dataclass

from src.domain.entities.base import Entity


@dataclass(kw_only=True)
class Trainer(Entity):
    tg_id: int
    name: str
    bio: str
    notification_chat_id: int
    is_active: bool