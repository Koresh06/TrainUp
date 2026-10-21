from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Column
from aiogram_dialog.widgets.text import Const, Format
from aiogram.types import CallbackQuery
from dishka.integrations.aiogram_dialog import inject, FromDishka

from src.application.mediator import Mediator
from src.application.use_cases.admin.get_overview_stats import (
    AdminOverviewStatsDTO,
    GetAdminOverviewStatsRequest,
)
from src.application.use_cases.stats.period import StatsPeriod
from src.presentation.telegram.features.admin.common import money
from src.presentation.telegram.features.admin.states import (
    AdminClientsSG,
    AdminExportSG,
    AdminFaqSG,
    AdminMailingSG,
    AdminMenuSG,
    AdminStatsSG,
    AdminTrainersSG,
)

ADMIN_MENU_TARGETS = {
    "stats": AdminStatsSG.main,
    "trainers": AdminTrainersSG.list,
    "clients": AdminClientsSG.search,
    "mailing": AdminMailingSG.target,
    "faq": AdminFaqSG.audience,
    "exports": AdminExportSG.main,
}


@inject
async def admin_menu_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    today: AdminOverviewStatsDTO = await mediator.handle(
        GetAdminOverviewStatsRequest(period=StatsPeriod.TODAY)
    )
    return {
        "trainers_total": today.trainers_total,
        "trainers_with_subscription": today.trainers_with_subscription,
        "clients_total": today.clients_total,
        "clients_new": today.clients_new,
        "trainings_today": today.trainings_completed + today.trainings_active,
        "revenue_today": money(today.revenue_period),
    }


async def on_admin_menu_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.start(state=ADMIN_MENU_TARGETS[button.widget_id])


admin_menu_dialog = Dialog(
    Window(
        Format(
            "🛠 <b>Панель администратора</b>\n\n"
            "👨‍🏫 Тренеров: <b>{trainers_total}</b> (с подпиской {trainers_with_subscription})\n"
            "👥 Клиентов: <b>{clients_total}</b> (+{clients_new} сегодня)\n"
            "🏋 Тренировок сегодня: <b>{trainings_today}</b>\n"
            "💰 Оплат сегодня: <b>{revenue_today}</b>"
        ),
        Column(
            Button(Const("📊 Статистика"), id="stats", on_click=on_admin_menu_click),
            Button(Const("👨‍🏫 Тренеры"), id="trainers", on_click=on_admin_menu_click),
            Button(Const("👥 Клиенты"), id="clients", on_click=on_admin_menu_click),
            Button(Const("📢 Рассылка"), id="mailing", on_click=on_admin_menu_click),
            Button(Const("❓ FAQ"), id="faq", on_click=on_admin_menu_click),
            Button(Const("📥 Выгрузки (CSV)"), id="exports", on_click=on_admin_menu_click),
        ),
        state=AdminMenuSG.main,
        getter=admin_menu_getter,
    ),
)
