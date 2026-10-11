from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, Row, ScrollingGroup, Select, SwitchTo
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.link_preview import LinkPreview

from .constants import RequestsFilter
from .getters import request_detail_getter, requests_list_getter
from .handlers import (
    can_close,
    can_reopen,
    can_take,
    on_change_status_click,
    on_filter_selected,
    on_request_selected,
)
from .states import TrainerRequestsSG

trainer_requests_dialog = Dialog(
    Window(
        Format("📨 <b>Заявки клиентов</b>{empty_hint}"),
        Row(
            *(
                Button(
                    Format(f"{{lbl_{f.value}}}"),
                    id=f.value,
                    on_click=on_filter_selected,
                )
                for f in RequestsFilter
            )
        ),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="requests_select",
                item_id_getter=lambda item: item["id"],
                items="requests",
                on_click=on_request_selected,
            ),
            id="requests_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        Cancel(Const("⬅️ Назад")),
        state=TrainerRequestsSG.list,
        getter=requests_list_getter,
    ),
    Window(
        Format(
            "{kind_label}\n"
            "<b>{title}</b>\n\n"
            "{details}\n\n"
            "👤 <b>Клиент:</b> {client_name}\n"
            "{contact_block}\n\n"
            "🕓 {created_at}\n"
            "📌 Статус: {status}"
        ),
        Button(
            Const("🛠 Взять в работу"),
            id="take_request",
            on_click=on_change_status_click,
            when=can_take,
        ),
        Button(
            Const("✅ Закрыть"),
            id="close_request",
            on_click=on_change_status_click,
            style=Style(style=ButtonStyle.SUCCESS),
            when=can_close,
        ),
        Button(
            Const("🔄 Вернуть в работу"),
            id="reopen_request",
            on_click=on_change_status_click,
            when=can_reopen,
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_list", state=TrainerRequestsSG.list),
        LinkPreview(is_disabled=True),
        state=TrainerRequestsSG.detail,
        getter=request_detail_getter,
    ),
)
