"""Общие подписи записей и дат для экранов тренера (расписание, карточка клиента)."""

from datetime import date, timedelta

from src.domain.enums.booking import BookingStatus
from src.domain.repositories.booking import BookingView
from src.domain.utils import get_project_today

WEEKDAY_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
WEEKDAY_FULL = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
MONTHS_GENITIVE = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]
MONTHS_NOMINATIVE = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]

STATUS_ICONS: dict[BookingStatus, str] = {
    BookingStatus.PENDING: "⏳",
    BookingStatus.CONFIRMED: "✅",
    BookingStatus.CANCELLED: "❌",
    BookingStatus.COMPLETED: "🏁",
    BookingStatus.NO_SHOW: "🚫",
}

STATUS_TITLES: dict[BookingStatus, str] = {
    BookingStatus.PENDING: "⏳ Ждёт подтверждения",
    BookingStatus.CONFIRMED: "✅ Подтверждена",
    BookingStatus.CANCELLED: "❌ Отменена",
    BookingStatus.COMPLETED: "🏁 Проведена",
    BookingStatus.NO_SHOW: "🚫 Клиент не пришёл",
}


def day_title(day: date) -> str:
    """«Сегодня, среда 22 октября» / «Пятница, 24 октября»."""
    today = get_project_today()
    base = f"{day.day} {MONTHS_GENITIVE[day.month - 1]}"
    weekday = WEEKDAY_FULL[day.weekday()]
    if day == today:
        return f"Сегодня, {weekday.lower()} {base}"
    if day == today + timedelta(days=1):
        return f"Завтра, {weekday.lower()} {base}"
    if day == today - timedelta(days=1):
        return f"Вчера, {weekday.lower()} {base}"
    return f"{weekday}, {base}"


def short_day(day: date) -> str:
    """«Ср 22.10»."""
    return f"{WEEKDAY_SHORT[day.weekday()]} {day.strftime('%d.%m')}"


def booking_badges(view: BookingView) -> str:
    badges = ""
    if view.booking.recurring_booking_id is not None:
        badges += " 🔁"
    if not view.client_has_telegram:
        badges += " 📵"
    return badges
