from datetime import date, datetime

from sqlalchemy import VARCHAR, BigInteger, Date, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.entities.bot_user import BotUser

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin


class BotUserModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "bot_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    blocked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    def to_entity(self) -> BotUser:
        return BotUser(
            id=self.id,
            tg_id=self.tg_id,
            username=self.username,
            first_name=self.first_name,
            last_activity_at=self.last_activity_at,
            blocked_at=self.blocked_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class BotUserActivityModel(BaseModel):
    """Один ряд на пользователя в день, когда он что-то делал в боте —
    из этого считаются DAU/WAU/MAU и график активности (last_activity_at
    в bot_users хранит только последний визит, историю не восстановить)."""

    __tablename__ = "bot_user_activity"

    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    activity_date: Mapped[date] = mapped_column(Date, primary_key=True, index=True)
