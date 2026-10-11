from datetime import date, datetime, time, timedelta
from enum import Enum

from src.domain.constants import PROJECT_TIMEZONE
from src.domain.utils import get_project_today


class StatsPeriod(str, Enum):
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    ALL = "all"


STATS_PERIOD_LABELS: dict[StatsPeriod, str] = {
    StatsPeriod.TODAY: "Сегодня",
    StatsPeriod.WEEK: "Неделя",
    StatsPeriod.MONTH: "Месяц",
    StatsPeriod.ALL: "Всё время",
}


def period_dates(period: StatsPeriod) -> tuple[date, date]:
    """[date_from; today] — неделя с понедельника, месяц с 1-го числа."""
    today = get_project_today()
    if period == StatsPeriod.TODAY:
        return today, today
    if period == StatsPeriod.WEEK:
        return today - timedelta(days=today.weekday()), today
    if period == StatsPeriod.MONTH:
        return today.replace(day=1), today
    return date(2000, 1, 1), today


def period_datetimes(period: StatsPeriod) -> tuple[datetime, datetime]:
    """То же в виде [начало date_from; начало дня после today) в поясе проекта —
    для сравнения с timestamptz-колонками (created_at)."""
    date_from, date_to = period_dates(period)
    return (
        datetime.combine(date_from, time.min, tzinfo=PROJECT_TIMEZONE),
        datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=PROJECT_TIMEZONE),
    )
