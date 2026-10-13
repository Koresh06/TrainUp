from dataclasses import dataclass
from datetime import datetime

from src.domain.entities.base import Entity


@dataclass(kw_only=True)
class BotUser(Entity):
    """Любой, кто писал боту — даже без регистрации тренером/клиентом.
    Нужен для аналитики админа: новые, активные, заблокировавшие бота."""

    tg_id: int
    username: str | None = None
    first_name: str | None = None
    last_activity_at: datetime | None = None
    # когда пользователь заблокировал бота (my_chat_member → kicked); None — не блокировал
    blocked_at: datetime | None = None

    @property
    def is_bot_blocked(self) -> bool:
        return self.blocked_at is not None
