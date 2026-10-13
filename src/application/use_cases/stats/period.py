from dataclasses import dataclass
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


# --- Временные ряды для графиков ---
# Отрезок графика не всегда совпадает с периодом статистики: «Сегодня» — это
# один столбик, поэтому график показывает последние 14 дней; «Всё время» —
# помесячно, чтобы не рисовать сотни столбиков.

TODAY_CHART_DAYS = 14
ALL_TIME_CHART_MAX_MONTHS = 24


@dataclass(frozen=True)
class ChartRange:
    date_from: date
    date_to: date
    by_month: bool

    def buckets(self) -> list[date]:
        result: list[date] = []
        current = self.date_from
        while current <= self.date_to:
            result.append(current)
            current = (
                (current.replace(day=1) + timedelta(days=32)).replace(day=1)
                if self.by_month
                else current + timedelta(days=1)
            )
        return result

    def bucket_of(self, day: date) -> date:
        return day.replace(day=1) if self.by_month else day

    def contains(self, day: date) -> bool:
        return self.date_from <= day <= self.date_to


def chart_range(period: StatsPeriod, first_day: date | None = None) -> ChartRange:
    """Неделя и месяц — целиком (включая будущие дни: видно запланированное),
    «Всё время» — с месяца первых данных, но не больше 24 месяцев."""
    today = get_project_today()
    if period == StatsPeriod.TODAY:
        return ChartRange(today - timedelta(days=TODAY_CHART_DAYS - 1), today, False)
    if period == StatsPeriod.WEEK:
        monday = today - timedelta(days=today.weekday())
        return ChartRange(monday, monday + timedelta(days=6), False)
    if period == StatsPeriod.MONTH:
        first = today.replace(day=1)
        last = (first + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return ChartRange(first, last, False)

    month = today.replace(day=1)
    earliest = month
    for _ in range(ALL_TIME_CHART_MAX_MONTHS - 1):
        earliest = (earliest - timedelta(days=1)).replace(day=1)
    start = max((first_day or month).replace(day=1), earliest)
    # минимум полгода на оси, чтобы у нового проекта не было одного столбика
    for _ in range(5):
        if (month.year - start.year) * 12 + month.month - start.month >= 5:
            break
        start = (start - timedelta(days=1)).replace(day=1)
    return ChartRange(start, today, True)
