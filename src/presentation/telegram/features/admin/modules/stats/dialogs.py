from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel, Row, SwitchTo
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from src.presentation.telegram.features.admin.common import on_admin_period_selected
from src.presentation.telegram.features.admin.states import AdminStatsSG
from src.presentation.telegram.features.trainer.stats.helper import (
    chart_group,
    on_chart_selected,
    period_row,
)

from .getters import (
    ADMIN_CHART_LABELS,
    admin_chart_getter,
    admin_stats_getter,
    admin_users_getter,
)

admin_stats_dialog = Dialog(
    Window(
        Format("{stats_text}"),
        Row(
            SwitchTo(
                Const("👥 Пользователи"),
                id="to_users",
                state=AdminStatsSG.users,
            ),
            SwitchTo(
                Const("📈 Графики"),
                id="to_charts",
                state=AdminStatsSG.charts,
            ),
        ),
        period_row(on_admin_period_selected),
        Cancel(Const("⬅️ Назад")),
        state=AdminStatsSG.main,
        getter=admin_stats_getter,
    ),
    Window(
        Format("{users_text}"),
        SwitchTo(
            Const("📈 Графики"),
            id="users_to_charts",
            state=AdminStatsSG.charts,
        ),
        period_row(on_admin_period_selected),
        SwitchTo(
            Const("⬅️ К общей статистике"),
            id="users_back",
            state=AdminStatsSG.main,
        ),
        state=AdminStatsSG.users,
        getter=admin_users_getter,
    ),
    Window(
        DynamicMedia("chart"),
        Format("{caption}"),
        chart_group(ADMIN_CHART_LABELS, on_chart_selected),
        period_row(on_admin_period_selected),
        Row(
            SwitchTo(
                Const("👥 Пользователи"),
                id="charts_to_users",
                state=AdminStatsSG.users,
            ),
            SwitchTo(
                Const("⬅️ К цифрам"),
                id="charts_back",
                state=AdminStatsSG.main,
            ),
        ),
        state=AdminStatsSG.charts,
        getter=admin_chart_getter,
    ),
)
