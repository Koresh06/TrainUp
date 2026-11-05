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
from src.application.use_cases.trainer.get_applications import (
    GetTrainerApplicationsRequest,
)
from src.domain.enums.admin import AdminPermission
from src.domain.enums.trainer import TrainerApprovalStatus
from src.presentation.telegram.features.admin.common import current_admin, money
from src.presentation.telegram.middlewares.access import NO_PERMISSION_TEXT
from src.presentation.telegram.features.admin.states import (
    AdminApplicationsSG,
    AdminClientsSG,
    AdminExportSG,
    AdminFaqSG,
    AdminMailingSG,
    AdminMenuSG,
    AdminNotificationsSG,
    AdminPricesSG,
    AdminStaffSG,
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
    "prices": AdminPricesSG.list,
    "applications": AdminApplicationsSG.list,
    "staff": AdminStaffSG.list,
    "notifications": AdminNotificationsSG.main,
}

# кнопка видна, если есть хотя бы одно из прав. «notifications» — всем админам,
# «staff» проверяется отдельно: это только супер-админ
ADMIN_MENU_PERMISSIONS: dict[str, tuple[AdminPermission, ...]] = {
    "applications": (AdminPermission.TRAINERS_APPROVE,),
    "stats": (AdminPermission.STATS,),
    "trainers": (AdminPermission.TRAINERS_VIEW,),
    "clients": (AdminPermission.CLIENTS_VIEW,),
    "mailing": (AdminPermission.MAILING,),
    "faq": (AdminPermission.FAQ,),
    "exports": (AdminPermission.EXPORTS,),
    "prices": (AdminPermission.PRICES,),
}


def _section_allowed(admin, section: str) -> bool:
    if admin is None:
        return False
    if section == "staff":
        return admin.is_super
    return section not in ADMIN_MENU_PERMISSIONS or admin.can(
        *ADMIN_MENU_PERMISSIONS[section]
    )


@inject
async def admin_menu_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    admin = current_admin(dialog_manager)
    sections = {
        f"can_{section}": _section_allowed(admin, section)
        for section in ADMIN_MENU_TARGETS
    }
    if sections["can_applications"]:
        trainers = await mediator.handle(GetTrainerApplicationsRequest())
        pending = sum(1 for t in trainers if t.approval_status == TrainerApprovalStatus.PENDING)
        sections["applications_label"] = f"🛂 Заявки тренеров ({pending})"
    else:
        sections["applications_label"] = ""

    # сводка с выручкой — та же статистика, без права её не показываем
    if not sections["can_stats"]:
        return {**sections, "summary": ""}

    today: AdminOverviewStatsDTO = await mediator.handle(
        GetAdminOverviewStatsRequest(period=StatsPeriod.TODAY)
    )
    return {
        **sections,
        "summary": (
            f"\n\n👨‍🏫 Тренеров: <b>{today.trainers_total}</b> "
            f"(с подпиской {today.trainers_with_subscription})\n"
            f"👥 Клиентов: <b>{today.clients_total}</b> (+{today.clients_new} сегодня)\n"
            f"🏋 Тренировок сегодня: "
            f"<b>{today.trainings_completed + today.trainings_active}</b>\n"
            f"💰 Оплат сегодня: <b>{money(today.revenue_period)}</b>"
        ),
    }


async def on_admin_menu_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    # окно могло быть открыто до того, как право отозвали
    if not _section_allowed(current_admin(dialog_manager), button.widget_id):
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return
    await dialog_manager.start(state=ADMIN_MENU_TARGETS[button.widget_id])


admin_menu_dialog = Dialog(
    Window(
        Format("🛠 <b>Панель администратора</b>{summary}"),
        Column(
            Button(Format("{applications_label}"), id="applications", on_click=on_admin_menu_click, when="can_applications"),
            Button(Const("📊 Статистика"), id="stats", on_click=on_admin_menu_click, when="can_stats"),
            Button(Const("👨‍🏫 Тренеры"), id="trainers", on_click=on_admin_menu_click, when="can_trainers"),
            Button(Const("👥 Клиенты"), id="clients", on_click=on_admin_menu_click, when="can_clients"),
            Button(Const("📢 Рассылка"), id="mailing", on_click=on_admin_menu_click, when="can_mailing"),
            Button(Const("❓ FAQ"), id="faq", on_click=on_admin_menu_click, when="can_faq"),
            Button(Const("📥 Выгрузки (CSV)"), id="exports", on_click=on_admin_menu_click, when="can_exports"),
            Button(Const("💲 Цены подписки"), id="prices", on_click=on_admin_menu_click, when="can_prices"),
            Button(Const("👮 Администраторы"), id="staff", on_click=on_admin_menu_click, when="can_staff"),
            Button(Const("🔔 Уведомления"), id="notifications", on_click=on_admin_menu_click, when="can_notifications"),
        ),
        state=AdminMenuSG.main,
        getter=admin_menu_getter,
    ),
)
