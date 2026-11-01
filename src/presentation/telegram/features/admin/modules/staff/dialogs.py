from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Cancel,
    Column,
    ScrollingGroup,
    Select,
    SwitchTo,
)
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Const, Format

from src.presentation.telegram.features.admin.states import AdminStaffSG
from src.presentation.telegram.features.error_handler import on_input_error

from .getters import admin_card_getter, admins_list_getter
from .handlers import (
    on_admin_query_entered,
    on_admin_selected,
    on_permission_toggled,
    on_remove_confirm,
    validate_admin_query,
)

admin_staff_dialog = Dialog(
    Window(
        Format(
            "👮 <b>Администраторы</b>\n\n"
            "Здесь вы решаете, кто помогает вести бот и что ему можно.{empty_hint}"
        ),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="admin_staff_select",
                item_id_getter=lambda item: item["id"],
                items="admins",
                on_click=on_admin_selected,
            ),
            id="admin_staff_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        SwitchTo(Const("➕ Добавить"), id="to_add", state=AdminStaffSG.add),
        Cancel(Const("⬅️ Назад")),
        state=AdminStaffSG.list,
        getter=admins_list_getter,
    ),
    Window(
        Const(
            "➕ <b>Новый администратор</b>\n\n"
            "Отправьте его Telegram ID или @username.\n\n"
            "<i>По @username бот найдёт только того, кто уже заходил в бота. "
            "Чтобы получать уведомления, человеку тоже нужно нажать /start.</i>"
        ),
        TextInput(
            id="admin_query_input",
            type_factory=validate_admin_query,
            on_success=on_admin_query_entered,
            on_error=on_input_error,
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_list", state=AdminStaffSG.list),
        state=AdminStaffSG.add,
    ),
    Window(
        Format("{card_text}"),
        Column(
            Select(
                Format("{item[label]}"),
                id="admin_permission_select",
                item_id_getter=lambda item: item["id"],
                items="permissions",
                on_click=on_permission_toggled,
            ),
        ),
        SwitchTo(
            Const("🗑 Удалить администратора"),
            id="to_remove",
            state=AdminStaffSG.remove_confirm,
            style=Style(style=ButtonStyle.DANGER),
        ),
        SwitchTo(Const("⬅️ К списку"), id="back_to_list", state=AdminStaffSG.list),
        state=AdminStaffSG.card,
        getter=admin_card_getter,
    ),
    Window(
        Const("Удалить администратора? Он сразу потеряет доступ к админке."),
        Button(
            Const("✅ Удалить"),
            id="remove_confirm",
            on_click=on_remove_confirm,
            style=Style(style=ButtonStyle.DANGER),
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_card", state=AdminStaffSG.card),
        state=AdminStaffSG.remove_confirm,
    ),
)
