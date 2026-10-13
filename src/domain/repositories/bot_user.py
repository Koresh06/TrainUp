from datetime import date, datetime
from typing import Protocol

from src.domain.entities.bot_user import BotUser


class BotUserRepository(Protocol):
    async def get_all(self) -> list[BotUser]: ...

    async def get_by_tg_id(self, tg_id: int) -> BotUser | None: ...

    async def touch_activity(
        self,
        *,
        tg_id: int,
        username: str | None,
        first_name: str | None,
        now: datetime,
        activity_date: date,
    ) -> None:
        """Атомарный upsert: создаёт пользователя при первом апдейте, обновляет
        last_activity_at, снимает отметку о блокировке (раз пишет — бот не
        заблокирован) и отмечает день активности (для DAU/WAU/MAU)."""
        ...

    async def set_bot_blocked(self, *, tg_id: int, blocked_at: datetime | None) -> None:
        """blocked_at=None — пользователь разблокировал бота. Upsert: блокировать
        может и тот, кого ещё нет в таблице (писал до появления аналитики)."""
        ...

    async def count_active(self, date_from: date, date_to: date) -> int:
        """Уникальные пользователи с активностью в [date_from; date_to]."""
        ...

    async def count_active_by_bucket(
        self, date_from: date, date_to: date, by_month: bool
    ) -> dict[date, int]:
        """Уникальные активные по дням (или по месяцам — ключ = 1-е число)."""
        ...
