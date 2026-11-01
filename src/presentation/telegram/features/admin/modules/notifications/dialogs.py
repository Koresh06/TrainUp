from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Cancel, Column, Select
from aiogram_dialog.widgets.text import Const, Format
from dishka.integrations.aiogram_dialog import inject, FromDishka

from src.application.mediator import Mediator
from src.application.use_cases.staff.notifications import (
    GetMutedNotificationsRequest,
    ToggleAdminNotificationRequest,
)
from src.domain.enums.admin import AdminNotification
from src.presentation.telegram.features.admin.common import current_admin
from src.presentation.telegram.features.admin.states import AdminNotificationsSG


@inject
async def admin_notifications_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    admin = current_admin(dialog_manager)
    muted = await mediator.handle(GetMutedNotificationsRequest(tg_id=admin.tg_id))
    # выключать можно только то, что вообще приходит этому админу
    available = [kind for kind in AdminNotification if admin.can(kind.required_permission)]
    return {
        "kinds": [
            {
                "id": kind.value,
                "label": f"{'🔕' if kind in muted else '🔔'} {kind.label()}",
            }
            for kind in available
        ],
        "hint": (
            "Нажмите на пункт, чтобы включить или выключить его.\n\n"
            "<i>Если заявки на ручную оплату выключат все, они всё равно придут "
            "супер-администратору — иначе тренер останется без подписки.</i>"
            if available
            else "Сейчас вам ничего не приходит: нет прав на оплаты и рассылки."
        ),
    }


@inject
async def on_notification_toggled(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
    mediator: FromDishka[Mediator],
) -> None:
    await mediator.handle(
        ToggleAdminNotificationRequest(
            tg_id=callback.from_user.id,
            kind=AdminNotification(item_id),
        )
    )


admin_notifications_dialog = Dialog(
    Window(
        Format("🔔 <b>Мои уведомления</b>\n\n{hint}"),
        Column(
            Select(
                Format("{item[label]}"),
                id="admin_notification_select",
                item_id_getter=lambda item: item["id"],
                items="kinds",
                on_click=on_notification_toggled,
            ),
        ),
        Cancel(Const("⬅️ Назад")),
        state=AdminNotificationsSG.main,
        getter=admin_notifications_getter,
    ),
)
