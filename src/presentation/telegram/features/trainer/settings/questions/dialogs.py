from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, Select, Group, Cancel, Back

from src.presentation.telegram.features.error_handler import on_input_error
from src.presentation.telegram.features.trainer.settings.questions.handlers import (
    on_question_selected,
)
from src.presentation.telegram.features.trainer.settings.questions.validaters import (
    validate_option_text,
    validate_question_label,
)

from .states import TrainerQuestionsSG
from .getters import question_detail_getter, questions_list_getter
from .handlers import (
    is_deletable_question,
    is_multi_select_question,
    on_add_option_click,
    on_add_question_click,
    on_delete_question_click,
    on_option_added,
    on_question_added,
    on_remove_option_click,
)

questions_dialog = Dialog(
    Window(
        Const(
            "📋 <b>Вопросы анкеты клиента</b>\n\n"
            "🔒 — системный вопрос, можно менять варианты, но не удалить.\n"
            "Остальные — ваши вопросы, можно удалить."
        ),
        Group(
            Select(
                Format("{item[label]}"),
                id="questions_select",
                item_id_getter=lambda item: item["id"],
                items="questions",
                on_click=on_question_selected,
            ),
            width=1,
        ),
        Button(
            Const("➕ Добавить свой вопрос"),
            id="add_question",
            on_click=on_add_question_click,
            style=Style(style=ButtonStyle.SUCCESS),
        ),
        Cancel(Const("⬅️ Назад")),
        state=TrainerQuestionsSG.main,
        getter=questions_list_getter,
    ),
    Window(
        Format("<b>{label}</b>\n\n" "Варианты ответа:\n{options_summary}"),
        Button(
            Const("➕ Добавить вариант"),
            id="add_option",
            on_click=on_add_option_click,
            when=is_multi_select_question,
        ),
        Button(
            Const("➖ Удалить последний вариант"),
            id="remove_option",
            on_click=on_remove_option_click,
            when=is_multi_select_question,
        ),
        Button(
            Const("🗑 Удалить вопрос"),
            id="delete_question",
            on_click=on_delete_question_click,
            style=Style(style=ButtonStyle.DANGER),
            when=is_deletable_question,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerQuestionsSG.question_detail,
        getter=question_detail_getter,
    ),
    Window(
        Const("Введите новый вариант ответа:"),
        TextInput(
            id="option_text_input",
            type_factory=validate_option_text,
            on_success=on_option_added,
            on_error=on_input_error,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerQuestionsSG.add_option,
    ),
    Window(
        Const(
            "✏️ <b>Новый вопрос</b>\n\n"
            "Введите текст вопроса. Клиент будет отвечать свободным текстом."
        ),
        TextInput(
            id="question_label_input",
            type_factory=validate_question_label,
            on_success=on_question_added,
            on_error=on_input_error,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerQuestionsSG.add_question,
    ),
)
