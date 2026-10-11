from collections.abc import Mapping
from datetime import datetime, timezone

from sqlalchemy import MetaData, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs


def _utc_now() -> datetime:
    # aware-время: naive в timestamptz Postgres трактует в часовом поясе сессии,
    # и created_at/updated_at «уезжали» на сервере с TZ, отличным от UTC
    return datetime.now(timezone.utc)


convention: Mapping[str, str] = {
    "ix": "ix__%(column_0_label)s",
    "uq": "uq__%(table_name)s__%(column_0_name)s",
    "ck": "ck__%(table_name)s__%(constraint_name)s",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "pk__%(table_name)s",
}
meta = MetaData(naming_convention=convention)


class BaseModel(AsyncAttrs, DeclarativeBase):
    metadata = meta


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        server_default=func.now(),
    )


class UpdatedAtMixin:
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
        server_default=func.now(),
    )