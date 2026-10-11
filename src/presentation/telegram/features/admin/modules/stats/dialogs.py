from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel
from aiogram_dialog.widgets.text import Const, Format

from src.presentation.telegram.features.admin.common import on_admin_period_selected
from src.presentation.telegram.features.admin.states import AdminStatsSG
from src.presentation.telegram.features.trainer.stats.helper import period_row

from .getters import admin_stats_getter

admin_stats_dialog = Dialog(
    Window(
        Format("{stats_text}"),
        period_row(on_admin_period_selected),
        Cancel(Const("⬅️ Назад")),
        state=AdminStatsSG.main,
        getter=admin_stats_getter,
    ),
)
