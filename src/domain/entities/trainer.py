from dataclasses import dataclass, field

from src.domain.entities.base import Entity


@dataclass(kw_only=True)
class Trainer(Entity):
    tg_id: int
    name: str
    bio: str
    notification_chat_id: int
    is_active: bool
    photo_file_id: str | None = None
    social_links: dict[str, str] = field(default_factory=dict)
    phone: str | None = None