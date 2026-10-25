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

from src.presentation.telegram.features.client.validaters import (
    validate_feedback_message,
)
from src.presentation.telegram.features.error_handler import on_input_error
from src.presentation.telegram.features.handlers_phone import validate_phone_number

from .getters import callback_confirm_getter, faq_answer_getter, faq_list_getter
from .handlers import (
    on_callback_confirm,
    on_callback_phone_entered,
    on_faq_item_selected,
    on_feedback_message_entered,
)
from .states import ClientFeedbackSG

client_feedback_dialog = Dialog(
    Window(
        Const("✉️ <b>Обратная связь</b>\n\nЧем можем помочь?"),
        Column(
            SwitchTo(
                Const("📞 Заказать обратный звонок"),
                id="to_callback",
                state=ClientFeedbackSG.callback_confirm,
            ),
            SwitchTo(
                Const("✉️ Написать тренеру"),
                id="to_message",
                state=ClientFeedbackSG.message,
            ),
            SwitchTo(
                Const("❓ Частые вопросы"),
                id="to_faq",
                state=ClientFeedbackSG.faq_list,
            ),
        ),
        Cancel(Const("⬅️ Назад")),
        state=ClientFeedbackSG.main,
    ),
    Window(
        Format("📞 Тренер перезвонит вам на номер <b>{phone}</b>.\n\nВсё верно?"),
        Button(
            Const("✅ Да, на этот номер"),
            id="callback_confirm",
            on_click=on_callback_confirm,
            style=Style(style=ButtonStyle.SUCCESS),
            when="has_phone",
        ),
        SwitchTo(
            Const("✏️ Указать другой номер"),
            id="to_callback_phone",
            state=ClientFeedbackSG.callback_phone,
        ),
        SwitchTo(
            Const("⬅️ Назад"),
            id="back_to_main",
            state=ClientFeedbackSG.main,
        ),
        state=ClientFeedbackSG.callback_confirm,
        getter=callback_confirm_getter,
    ),
    Window(
        Const(
            "📞 Введите номер для обратного звонка "
            "(например, +375291234567 или 80291234567):"
        ),
        TextInput(
            id="callback_phone_input",
            type_factory=validate_phone_number,
            on_success=on_callback_phone_entered,
            on_error=on_input_error,
        ),
        SwitchTo(
            Const("⬅️ Назад"),
            id="back_to_callback",
            state=ClientFeedbackSG.callback_confirm,
        ),
        state=ClientFeedbackSG.callback_phone,
    ),
    Window(
        Const("✉️ Напишите сообщение тренеру — он получит его и ответит вам лично:"),
        TextInput(
            id="feedback_message_input",
            type_factory=validate_feedback_message,
            on_success=on_feedback_message_entered,
            on_error=on_input_error,
        ),
        SwitchTo(
            Const("⬅️ Назад"),
            id="back_to_main",
            state=ClientFeedbackSG.main,
        ),
        state=ClientFeedbackSG.message,
    ),
    Window(
        Format("❓ <b>Частые вопросы</b>{empty_hint}"),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="faq_select",
                item_id_getter=lambda item: item["id"],
                items="faq_items",
                on_click=on_faq_item_selected,
            ),
            id="faq_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        SwitchTo(
            Const("⬅️ Назад"),
            id="back_to_main",
            state=ClientFeedbackSG.main,
        ),
        state=ClientFeedbackSG.faq_list,
        getter=faq_list_getter,
    ),
    Window(
        Format("❓ <b>{question}</b>\n\n{answer}"),
        SwitchTo(
            Const("⬅️ К вопросам"),
            id="back_to_faq",
            state=ClientFeedbackSG.faq_list,
        ),
        state=ClientFeedbackSG.faq_answer,
        getter=faq_answer_getter,
    ),
)
