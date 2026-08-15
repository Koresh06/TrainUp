from datetime import datetime, timedelta, timezone

MOSCOW_TZ = timezone(timedelta(hours=3))


def to_moscow(dt: datetime) -> datetime:
    return dt.astimezone(MOSCOW_TZ)