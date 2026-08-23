from datetime import date, timedelta
from dishka import AsyncContainer
from dishka.integrations.aiogram_dialog import CONTAINER_NAME

from aiogram.enums import ButtonStyle
from aiogram.types import InlineKeyboardButton
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.text import Text
from aiogram_dialog.widgets.kbd import (
    Calendar,
    CalendarConfig,
    CalendarScope,
)
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.kbd.calendar_kbd import (
    DATE_TEXT,
    TODAY_TEXT,
    CalendarDaysView,
    CalendarScopeView,
    CalendarUserConfig,
)

from src.application.mediator import Mediator
from src.domain.constants import DEFAULT_CALENDAR_HORIZON_DAYS
from src.domain.entities.trainer_booking_settings import TrainerBookingSettings
from src.application.use_cases.trainer_booking_settings.get_by_id import (
    GetTrainerBookingSettingsRequest,
)

from .dynamic_style import DynamicStyle


HORIZON_CACHE_KEY = "calendar_horizon_days"
AVAILABILITY_CACHE_KEY = "day_availability"


class WeekDayRu(Text):
    WEEKDAYS = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]

    async def _render_text(self, data, manager: DialogManager) -> str:
        selected_date: date = data["date"]
        return self.WEEKDAYS[selected_date.weekday()]


class MonthNavText(Text):
    MONTHS = [
        "янв",
        "фев",
        "мар",
        "апр",
        "май",
        "июн",
        "июл",
        "авг",
        "сен",
        "окт",
        "ноя",
        "дек",
    ]

    def __init__(self, prefix: str = "", suffix: str = "") -> None:
        super().__init__()
        self._prefix = prefix
        self._suffix = suffix

    async def _render_text(self, data, manager: DialogManager) -> str:
        target_date: date = data["date"]
        month_name = self.MONTHS[target_date.month - 1]
        return f"{self._prefix}{month_name} {target_date.year}{self._suffix}"


def _is_day_in_window(current_date: date, manager: DialogManager) -> bool:
    today = date.today()
    horizon_days: int = manager.dialog_data.get(
        HORIZON_CACHE_KEY,
        DEFAULT_CALENDAR_HORIZON_DAYS,
    )
    return today <= current_date <= today + timedelta(days=horizon_days)


def is_day_available(data: dict, widget, manager: DialogManager) -> bool:
    current_date: date = data["date"]
    if not _is_day_in_window(current_date, manager):
        return False
    availability: dict[str, int] = manager.dialog_data.get(AVAILABILITY_CACHE_KEY, {})
    return availability.get(current_date.isoformat(), 0) > 0


def is_day_unavailable(data: dict, widget, manager: DialogManager) -> bool:
    return not is_day_available(data, widget, manager)


def _day_style(data: dict, manager: DialogManager) -> ButtonStyle:
    current_date: date = data["date"]

    if not _is_day_in_window(current_date, manager):
        return ButtonStyle.DANGER

    availability: dict[str, int] = manager.dialog_data.get(AVAILABILITY_CACHE_KEY, {})
    has_free = availability.get(current_date.isoformat(), 0) > 0
    return ButtonStyle.SUCCESS if has_free else ButtonStyle.DANGER



day_style = DynamicStyle(_day_style)


class BookingDaysView(CalendarDaysView):
    async def render(
        self,
        config: CalendarConfig,
        offset: date,
        data: dict,
        manager: DialogManager,
    ) -> list[list[InlineKeyboardButton]]:
        rows = await super().render(config, offset, data, manager)
        return rows[1:]


class BookingCalendar(Calendar):
    def _init_views(self) -> dict[CalendarScope, CalendarScopeView]:
        return {
            CalendarScope.DAYS: BookingDaysView(
                self._item_callback_data,
                date_text=DATE_TEXT,
                today_text=TODAY_TEXT,
                weekday_text=WeekDayRu(),
                next_month_text=MonthNavText(suffix=" >>"),
                prev_month_text=MonthNavText(prefix="<< "),
                weekday_style=Style(ButtonStyle.PRIMARY),
                date_style=day_style,
                today_style=day_style,
            ),
        }

    async def _get_user_config(
        self,
        data: dict,
        manager: DialogManager,
    ) -> CalendarUserConfig:
        container: AsyncContainer = manager.middleware_data[CONTAINER_NAME]
        mediator = await container.get(Mediator)

        trainer_id: int = manager.start_data["trainer_id"]
        settings: TrainerBookingSettings = await mediator.handle(
            GetTrainerBookingSettingsRequest(trainer_id=trainer_id)
        )

        today = date.today()
        return CalendarUserConfig(
            min_date=today,
            max_date=today + timedelta(days=settings.calendar_horizon_days),
        )
