from aiogram.enums import ButtonStyle, ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Group, Select
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Const, Format

from src.presentation.telegram.features.client.questionnaire import (
    has_text_answer,
    on_option_toggle,
)
from src.presentation.telegram.features.client.register.getters import (
    is_multi_select,
    questions_getter,
)

from .getters import answers_confirm_getter, client_profile_getter
from .handlers import (
    on_answers_save,
    on_confirm_back,
    on_keep_text_answer,
    on_edit_answers_click,
    on_multi_select_next,
    on_question_back,
    on_text_answer,
)
from .states import ClientProfileSG

client_profile_dialog = Dialog(
    Window(
        Format(
            "📝 <b>Моя анкета</b>\n\n"
            "{packages_block}"
            "👤 <b>{full_name}</b>\n"
            "📞 {phone}\n"
            "🎂 {age}\n"
            "🏋️ Стаж: {sport_experience}\n\n"
            "{answers_summary}\n\n"
            "<i>Тренер видит ваши цели и пожелания при каждой записи — "
            "держите их актуальными.</i>"
        ),
        Button(
            Const("✏️ Обновить ответы"),
            id="edit_answers",
            on_click=on_edit_answers_click,
        ),
        Cancel(Const("⬅️ Назад")),
        state=ClientProfileSG.main,
        getter=client_profile_getter,
    ),
    Window(
        Format("<b>{question_label}</b>{question_hint}"),
        Group(
            Select(
                Format("{item[label]}"),
                id="profile_question_options_select",
                item_id_getter=lambda item: item["id"],
                items="options",
                on_click=on_option_toggle,
            ),
            width=1,
            when=is_multi_select,
        ),
        MessageInput(
            func=on_text_answer,
            content_types=[ContentType.TEXT],
        ),
        Button(
            Const("Далее ➡️"),
            id="profile_question_next",
            on_click=on_multi_select_next,
            style=Style(style=ButtonStyle.SUCCESS),
            when=is_multi_select,
        ),
        Button(
            Const("Оставить как есть ➡️"),
            id="profile_question_keep_text",
            on_click=on_keep_text_answer,
            when=has_text_answer,
        ),
        Button(
            Const("⬅️ Назад"),
            id="profile_question_back",
            on_click=on_question_back,
        ),
        state=ClientProfileSG.questions,
        getter=questions_getter,
    ),
    Window(
        Format("✅ <b>Проверьте ответы</b>\n\n{answers_summary}"),
        Button(
            Const("💾 Сохранить"),
            id="save_answers",
            on_click=on_answers_save,
            style=Style(style=ButtonStyle.SUCCESS),
        ),
        Button(Const("⬅️ Назад"), id="answers_confirm_back", on_click=on_confirm_back),
        state=ClientProfileSG.confirm,
        getter=answers_confirm_getter,
    ),
)
