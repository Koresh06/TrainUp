from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, Cancel, ScrollingGroup, Select, SwitchTo
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.link_preview import LinkPreview

from src.presentation.telegram.features.admin.states import AdminClientsSG
from src.presentation.telegram.features.error_handler import on_input_error

from .getters import admin_client_card_getter, admin_clients_list_getter
from .handlers import (
    on_client_selected,
    on_clients_query_entered,
    on_recent_clients_click,
    on_toggle_client_block,
    validate_clients_query,
)

admin_clients_dialog = Dialog(
    Window(
        Const(
            "👥 <b>Клиенты</b>\n\n"
            "Отправьте имя, телефон, @username или Telegram ID для поиска."
        ),
        TextInput(
            id="clients_query_input",
            type_factory=validate_clients_query,
            on_success=on_clients_query_entered,
            on_error=on_input_error,
        ),
        Button(
            Const("🆕 Последние зарегистрированные"),
            id="recent_clients",
            on_click=on_recent_clients_click,
        ),
        Cancel(Const("⬅️ Назад")),
        state=AdminClientsSG.search,
    ),
    Window(
        Format("{title}{empty_hint}"),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="admin_clients_select",
                item_id_getter=lambda item: item["id"],
                items="clients",
                on_click=on_client_selected,
            ),
            id="admin_clients_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        SwitchTo(Const("🔎 Новый поиск"), id="to_search", state=AdminClientsSG.search),
        state=AdminClientsSG.list,
        getter=admin_clients_list_getter,
    ),
    Window(
        Format("{card_text}"),
        Button(
            Const("⛔ Заблокировать"),
            id="block_client",
            on_click=on_toggle_client_block,
            style=Style(style=ButtonStyle.DANGER),
            when="is_active",
        ),
        Button(
            Const("✅ Разблокировать"),
            id="unblock_client",
            on_click=on_toggle_client_block,
            style=Style(style=ButtonStyle.SUCCESS),
            when="is_blocked",
        ),
        SwitchTo(Const("⬅️ К списку"), id="back_to_list", state=AdminClientsSG.list),
        LinkPreview(is_disabled=True),
        state=AdminClientsSG.card,
        getter=admin_client_card_getter,
    ),
)
