from dataclasses import dataclass, field
from datetime import datetime

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
    # реферальная программа тренеров: свой код для ссылки «пригласить тренера»,
    # кто пригласил этого тренера и когда пригласившему начислен бонус
    referral_code: str | None = None
    referred_by_trainer_id: int | None = None
    referral_rewarded_at: datetime | None = None