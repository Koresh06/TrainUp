import re

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Select
from dishka.integrations.aiogram_dialog import inject, FromDishka

from src.application.mediator import Mediator
from src.application.use_cases.staff.manage import (
    AddAdminRequest,
    RemoveAdminRequest,
    ToggleAdminPermissionRequest,
)
from src.domain.entities.bot_admin import BotAdmin
from src.domain.enums.admin import AdminPermission
from src.domain.exception.admin import (
    AdminAlreadyExistsException,
    AdminUserNotFoundException,
)
from src.presentation.telegram.features.admin.states import AdminStaffSG

MAX_TG_ID = 2**63 - 1
USERNAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{3,31}")


def validate_admin_query(value: str) -> str:
    value = value.strip().removeprefix("@")
    if value.isdecimal() and 0 < int(value) <= MAX_TG_ID:
        return value
    if USERNAME_RE.fullmatch(value):
        return value
    raise ValueError("Отправьте числовой Telegram ID или @username")


async def on_admin_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["admin_tg_id"] = int(item_id)
    await dialog_manager.switch_to(AdminStaffSG.card)


@inject
async def on_admin_query_entered(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    value: str,
    mediator: FromDishka[Mediator],
) -> None:
    by_id = value.isdecimal()
    try:
        admin: BotAdmin = await mediator.handle(
            AddAdminRequest(
                added_by_tg_id=message.from_user.id,
                tg_id=int(value) if by_id else None,
                username=None if by_id else value,
            )
        )
    except (AdminAlreadyExistsException, AdminUserNotFoundException) as error:
        await message.answer(f"❌ {error.message}")
        return
    dialog_manager.dialog_data["admin_tg_id"] = admin.tg_id
    await dialog_manager.switch_to(AdminStaffSG.card)


@inject
async def on_permission_toggled(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
    mediator: FromDishka[Mediator],
) -> None:
    await mediator.handle(
        ToggleAdminPermissionRequest(
            tg_id=dialog_manager.dialog_data["admin_tg_id"],
            permission=AdminPermission(item_id),
        )
    )


@inject
async def on_remove_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    await mediator.handle(
        RemoveAdminRequest(tg_id=dialog_manager.dialog_data["admin_tg_id"])
    )
    await callback.answer("Администратор удалён")
    await dialog_manager.switch_to(AdminStaffSG.list)
