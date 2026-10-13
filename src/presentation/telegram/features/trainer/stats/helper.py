from enum import Enum
from typing import Callable
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Row, Button
from aiogram_dialog.widgets.text import Format

from src.application.use_cases.stats.get_trainer import StatsPeriod


def period_flags(period: StatsPeriod) -> dict:
    return {
        "is_today": period == StatsPeriod.TODAY,
        "is_week": period == StatsPeriod.WEEK,
        "is_month": period == StatsPeriod.MONTH,
        "is_all": period == StatsPeriod.ALL,
        "lbl_today": ("🟢 " if period == StatsPeriod.TODAY else "") + "Сегодня",
        "lbl_week": ("🟢 " if period == StatsPeriod.WEEK else "") + "Неделя",
        "lbl_month": ("🟢 " if period == StatsPeriod.MONTH else "") + "Месяц",
        "lbl_all": ("🟢 " if period == StatsPeriod.ALL else "") + "Всё",
    }


def period_row(on_period_selected: Callable) -> Row:
    return Row(
        Button(Format("{lbl_today}"), id="today", on_click=on_period_selected),
        Button(Format("{lbl_week}"), id="week", on_click=on_period_selected),
        Button(Format("{lbl_month}"), id="month", on_click=on_period_selected),
        Button(Format("{lbl_all}"), id="all", on_click=on_period_selected),
    )


class ScopePrivate(str, Enum):
    GENERAL = "general"
    TRAINER = "trainer"


def current_period(dialog_manager: DialogManager, scope: ScopePrivate) -> StatsPeriod:
    raw = dialog_manager.dialog_data.get(
        f"period_{scope.value}", StatsPeriod.MONTH.value
    )
    return StatsPeriod(raw)


# --- Переключатель графиков (общий для тренера и админки) ---

CHART_KEY = "chart"


class TrainerChart(str, Enum):
    TRAININGS = "trainings"
    INCOME = "income"
    LOAD = "load"


TRAINER_CHART_LABELS: dict[TrainerChart, str] = {
    TrainerChart.TRAININGS: "🏋 Тренировки",
    TrainerChart.INCOME: "💰 Доход",
    TrainerChart.LOAD: "🗓 Загрузка",
}


def selected_label(label: str, selected: bool) -> str:
    return ("🟢 " if selected else "") + label


def chart_flags(chart: Enum, labels: dict | None = None) -> dict:
    """lbl_chart_<id> для кнопок переключателя графиков."""
    labels = labels or TRAINER_CHART_LABELS
    return {
        f"lbl_chart_{item.value}": selected_label(label, item == chart)
        for item, label in labels.items()
    }


def chart_row(labels: dict, on_chart_selected: Callable) -> Row:
    return Row(
        *(
            Button(
                Format(f"{{lbl_chart_{item.value}}}"),
                id=f"chart_{item.value}",
                on_click=on_chart_selected,
            )
            for item in labels
        )
    )


def current_chart(
    dialog_manager: DialogManager, chart_type: type[Enum] = TrainerChart
) -> Enum:
    raw = dialog_manager.dialog_data.get(CHART_KEY)
    try:
        return chart_type(raw)
    except ValueError:
        return next(iter(chart_type))


async def on_chart_selected(callback, button: Button, dialog_manager: DialogManager) -> None:
    dialog_manager.dialog_data[CHART_KEY] = button.widget_id.removeprefix("chart_")
