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

from src.presentation.telegram.features.admin.states import AdminFaqSG
from src.presentation.telegram.features.error_handler import on_input_error

from .getters import (
    FAQ_AUDIENCE_LABELS,
    admin_faq_detail_getter,
    admin_faq_list_getter,
    admin_faq_new_question_getter,
)
from .handlers import (
    on_faq_answer_entered,
    on_faq_audience_selected,
    on_faq_delete_click,
    on_faq_item_selected,
    on_faq_question_entered,
    validate_faq_answer,
    validate_faq_question,
)

admin_faq_dialog = Dialog(
    Window(
        Const("❓ <b>FAQ</b>\n\nКакой раздел редактируем?"),
        Column(
            *(
                Button(
                    Const(label), id=audience.value, on_click=on_faq_audience_selected
                )
                for audience, label in FAQ_AUDIENCE_LABELS.items()
            )
        ),
        Cancel(Const("⬅️ Назад")),
        state=AdminFaqSG.audience,
    ),
    Window(
        Format("<b>{audience_label}</b>\n{audience_hint}{empty_hint}"),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="admin_faq_select",
                item_id_getter=lambda item: item["id"],
                items="faq_items",
                on_click=on_faq_item_selected,
            ),
            id="admin_faq_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        SwitchTo(
            Const("➕ Добавить вопрос"),
            id="add_faq",
            state=AdminFaqSG.add_question,
            style=Style(style=ButtonStyle.SUCCESS),
        ),
        SwitchTo(
            Const("⬅️ Назад"),
            id="back_to_audience",
            state=AdminFaqSG.audience,
        ),
        state=AdminFaqSG.list,
        getter=admin_faq_list_getter,
    ),
    Window(
        Format("❓ <b>{question}</b>\n\n{answer}"),
        Button(
            Const("🗑 Удалить"),
            id="delete_faq",
            on_click=on_faq_delete_click,
            style=Style(style=ButtonStyle.DANGER),
        ),
        SwitchTo(
            Const("⬅️ Назад"),
            id="back_to_list",
            state=AdminFaqSG.list,
        ),
        state=AdminFaqSG.detail,
        getter=admin_faq_detail_getter,
    ),
    Window(
        Const("✏️ Введите текст вопроса:"),
        TextInput(
            id="faq_question_input",
            type_factory=validate_faq_question,
            on_success=on_faq_question_entered,
            on_error=on_input_error,
        ),
        SwitchTo(
            Const("⬅️ Назад"),
            id="back_to_list",
            state=AdminFaqSG.list,
        ),
        state=AdminFaqSG.add_question,
    ),
    Window(
        Format("❓ <b>{new_question}</b>\n\n✏️ Теперь введите ответ:"),
        TextInput(
            id="faq_answer_input",
            type_factory=validate_faq_answer,
            on_success=on_faq_answer_entered,
            on_error=on_input_error,
        ),
        SwitchTo(
            Const("⬅️ Назад"),
            id="back_to_question",
            state=AdminFaqSG.add_question,
        ),
        state=AdminFaqSG.add_answer,
        getter=admin_faq_new_question_getter,
    ),
)
