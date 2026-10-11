from datetime import datetime, timezone

from src.domain.constants import PROJECT_TIMEZONE


def to_moscow(dt: datetime) -> datetime:
    """Перевод в часовой пояс проекта для отображения (naive считаем UTC)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(PROJECT_TIMEZONE)
