from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel, SwitchTo
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from .states import TrainerStatsSG
from .getters import stats_chart_getter, stats_getter
from .handlers import on_period_selected
from .helper import TRAINER_CHART_LABELS, chart_row, on_chart_selected, period_row

trainer_stats_dialog = Dialog(
    Window(
        Format("{stats_text}"),
        SwitchTo(Const("📈 Графики"), id="to_charts", state=TrainerStatsSG.charts),
        period_row(on_period_selected),
        Cancel(Const("⬅️ Назад")),
        state=TrainerStatsSG.main,
        getter=stats_getter,
    ),
    Window(
        DynamicMedia("chart"),
        Format("{caption}"),
        chart_row(TRAINER_CHART_LABELS, on_chart_selected),
        period_row(on_period_selected),
        SwitchTo(Const("⬅️ К цифрам"), id="to_stats", state=TrainerStatsSG.main),
        state=TrainerStatsSG.charts,
        getter=stats_chart_getter,
    ),
)
