"""Мелкие форматтеры для подписей статистики."""

from decimal import Decimal

from src.application.use_cases.stats.period import ChartRange, StatsPeriod
from src.presentation.telegram.charts.render import WEEKDAYS_SHORT
MONTHS_NOMINATIVE = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]


def number(value: Decimal | int | float) -> str:
    """12 345 — пробел как разделитель тысяч, без копеек у целых."""
    value = Decimal(value)
    text = f"{value:,.0f}" if value == value.to_integral() else f"{value:,.2f}"
    return text.replace(",", " ")


def byn(value: Decimal | int) -> str:
    return f"{number(value)} BYN"


def chart_period_label(period: StatsPeriod, rng: ChartRange) -> str:
    if period == StatsPeriod.TODAY:
        return "последние 14 дней"
    if period == StatsPeriod.WEEK:
        return f"неделя {rng.date_from:%d.%m}–{rng.date_to:%d.%m}"
    if period == StatsPeriod.MONTH:
        return f"{MONTHS_NOMINATIVE[rng.date_from.month - 1]} {rng.date_from.year}"
    return f"по месяцам с {rng.date_from:%m.%Y}"


def hours_label(hours: list[int]) -> str:
    return ", ".join(f"{h:02d}:00" for h in sorted(hours)) or "—"


def weekdays_label(weekdays: list[int]) -> str:
    return ", ".join(WEEKDAYS_SHORT[d] for d in sorted(weekdays)) or "—"
