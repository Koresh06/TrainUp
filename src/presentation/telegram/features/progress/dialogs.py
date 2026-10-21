from aiogram import F
from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Row, ScrollingGroup, Select, SwitchTo
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from src.presentation.telegram.features.error_handler import on_input_error

from .getters import (
    chart_getter,
    delete_confirm_getter,
    photo_getter,
    photos_getter,
    progress_getter,
)
from .handlers import (
    on_chart_kind,
    on_delete_last,
    on_only_photo,
    on_photo_received,
    on_photo_selected,
    on_progress_start,
    on_save_without_photo,
    on_values_input,
)
from .states import ProgressSG
from .validaters import parse_measurement

to_main = SwitchTo(Const("⬅️ Назад"), id="to_main", state=ProgressSG.main)

progress_dialog = Dialog(
    Window(
        Format("{text}"),
        SwitchTo(Const("➕ Новая запись"), id="add", state=ProgressSG.add),
        Row(
            SwitchTo(Const("📊 График"), id="chart", state=ProgressSG.chart, when="has_chart"),
            SwitchTo(
                Format("🖼 Фото ({photos_count})"),
                id="photos",
                state=ProgressSG.photos,
                when="has_photos",
            ),
        ),
        SwitchTo(
            Const("🗑 Удалить последнюю"),
            id="delete",
            state=ProgressSG.delete_confirm,
            when="has_items",
        ),
        Cancel(Const("⬅️ Назад")),
        state=ProgressSG.main,
        getter=progress_getter,
    ),
    Window(
        DynamicMedia("chart"),
        Format("{caption}"),
        Row(
            Button(Const("⚖️ Вес"), id="weight", on_click=on_chart_kind, when=~F["is_weight"]),
            Button(Const("📏 Обхваты"), id="girth", on_click=on_chart_kind, when="is_weight"),
        ),
        to_main,
        state=ProgressSG.chart,
        getter=chart_getter,
    ),
    Window(
        Const(
            "➕ <b>Новая запись</b>\n\n"
            "Отправьте вес или замеры через пробел в порядке: "
            "<b>вес талия грудь бёдра</b>.\n"
            "Например: <code>72.5</code> или <code>72.5 80 95 98</code>.\n"
            "Пропустить значение — «-»: <code>- 80</code>. Можно и словами: "
            "<code>талия 80</code>."
        ),
        TextInput(
            id="values_input",
            type_factory=parse_measurement,
            on_success=on_values_input,
            on_error=on_input_error,
        ),
        Button(Const("📷 Только фото"), id="only_photo", on_click=on_only_photo),
        to_main,
        state=ProgressSG.add,
    ),
    Window(
        Const("📷 Прикрепите фото (по желанию) — потом удобно сравнивать «до/после»."),
        MessageInput(func=on_photo_received, content_types=[ContentType.PHOTO]),
        Button(Const("✅ Сохранить без фото"), id="save", on_click=on_save_without_photo),
        SwitchTo(Const("⬅️ Назад"), id="back_to_add", state=ProgressSG.add),
        state=ProgressSG.add_photo,
    ),
    Window(
        Const("🖼 <b>Фото</b>"),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="photos_select",
                item_id_getter=lambda item: item["id"],
                items="photos",
                on_click=on_photo_selected,
            ),
            id="photos_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        to_main,
        state=ProgressSG.photos,
        getter=photos_getter,
    ),
    Window(
        DynamicMedia("photo"),
        Format("{caption}"),
        SwitchTo(Const("⬅️ К фото"), id="to_photos", state=ProgressSG.photos),
        state=ProgressSG.photo,
        getter=photo_getter,
    ),
    Window(
        Format("🗑 Удалить последнюю запись?\n\n{entry}"),
        Button(Const("🗑 Удалить"), id="delete_yes", on_click=on_delete_last),
        to_main,
        state=ProgressSG.delete_confirm,
        getter=delete_confirm_getter,
    ),
    on_start=on_progress_start,
)
