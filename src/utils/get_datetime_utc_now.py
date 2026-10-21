from datetime import datetime, timezone


def get_datetime_utc_now() -> datetime:
    datetime_now = datetime.now(tz=timezone.utc)
    return datetime_now.replace(tzinfo=None)

def get_aware_utc_now() -> datetime:
    """Aware-время для колонок timestamptz: naive Postgres трактует в часовом
    поясе сессии (см. models/base.py)."""
    return datetime.now(tz=timezone.utc)
