from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Select

from src.domain.constants import OTHER_OPTION_TEXT_MAX_LENGTH
from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.enums.question_type import QuestionType
from src.presentation.telegram.features.client.register.helpers import (
    _build_multi_select_answer,
    _current_question,
    _other_option_selected,
    _restore_selected,
    is_other_option,
)

# Пошаговое прохождение вопросов анкеты тренера (MULTI_SELECT / TEXT).
# Используется при регистрации клиента и при обновлении анкеты из меню —
# отличаются только состояния, между которыми ходит диалог.


def has_text_answer(data: dict, widget, manager: DialogManager) -> bool:
    return data.get("has_text_answer", False)


def load_questions(
    dialog_data: dict,
    questions: list[RegistrationQuestion],
    answers: dict[str, list[str]] | None = None,
) -> None:
    dialog_data["questions"] = [
        {
            "id": q.id,
            "type": q.question_type.value,
            "label": q.label,
            "options": q.options,
        }
        for q in questions
    ]
    dialog_data["question_index"] = 0
    dialog_data["answers"] = dict(answers or {})  # question_id (str) -> list[str]
    _restore_selected(dialog_data)  # индексы выбранных опций текущего MULTI_SELECT


async def on_option_toggle(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    index = int(item_id)
    data = dialog_manager.dialog_data
    selected: list[int] = data.setdefault("current_selected", [])
    if index in selected:
        selected.remove(index)
        question = _current_question(data)
        if question is not None and is_other_option(question["options"][index]):
            data["current_other_text"] = None
    else:
        selected.append(index)


@dataclass(frozen=True)
class QuestionnaireHandlers:
    on_multi_select_next: Callable[..., Awaitable[None]]
    on_question_back: Callable[..., Awaitable[None]]
    on_text_answer: Callable[..., Awaitable[None]]
    on_confirm_back: Callable[..., Awaitable[None]]
    on_keep_text_answer: Callable[..., Awaitable[None]]


def make_questionnaire_handlers(
    *,
    questions_state: State,
    done_state: State,
    exit_state: State,
) -> QuestionnaireHandlers:
    """
    questions_state — окно с текущим вопросом, done_state — куда перейти после
    последнего вопроса, exit_state — куда вернуться «Назад» с первого вопроса.
    """

    async def advance_question(dialog_manager: DialogManager) -> None:
        dialog_manager.dialog_data["question_index"] += 1
        _restore_selected(dialog_manager.dialog_data)

        if _current_question(dialog_manager.dialog_data) is None:
            await dialog_manager.switch_to(done_state)
        else:
            await dialog_manager.switch_to(questions_state)

    async def on_multi_select_next(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager,
    ) -> None:
        data = dialog_manager.dialog_data
        question = _current_question(data)
        if question is None:
            return

        selected: list[int] = data.get("current_selected", [])
        if not selected:
            await callback.answer("Выбери хотя бы один вариант", show_alert=True)
            return
        if _other_option_selected(data, question) and not data.get("current_other_text"):
            await callback.answer(
                "Вы выбрали «Другое» — напишите сообщением, что именно",
                show_alert=True,
            )
            return

        data["answers"][str(question["id"])] = _build_multi_select_answer(data, question)
        await advance_question(dialog_manager)

    async def on_question_back(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager,
    ) -> None:
        data = dialog_manager.dialog_data
        index = data.get("question_index", 0)

        if index > 0:
            data["question_index"] = index - 1
            _restore_selected(data)
            await dialog_manager.switch_to(questions_state)
        else:
            await dialog_manager.switch_to(exit_state)

    async def on_text_answer(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager,
    ) -> None:
        data = dialog_manager.dialog_data
        question = _current_question(data)
        if question is None:
            return

        text = (message.text or "").strip()
        if not text:
            await message.answer("Введите текст ответа")
            return

        if question["type"] == QuestionType.MULTI_SELECT.value:
            # в MULTI_SELECT текст принимается только как расшифровка «Другое»
            if not _other_option_selected(data, question):
                await message.answer(
                    "Выберите варианты кнопками. Чтобы указать свой — выберите «Другое»."
                )
                return
            if len(text) > OTHER_OPTION_TEXT_MAX_LENGTH:
                await message.answer(
                    f"Слишком длинно (макс. {OTHER_OPTION_TEXT_MAX_LENGTH} символов)"
                )
                return
            data["current_other_text"] = text
            return

        data["answers"][str(question["id"])] = [text]
        await advance_question(dialog_manager)

    async def on_confirm_back(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager,
    ) -> None:
        # «Назад» с итогового экрана — на последний вопрос, а не в пустое окно
        data = dialog_manager.dialog_data
        questions: list[dict] = data.get("questions", [])
        if not questions:
            await dialog_manager.switch_to(exit_state)
            return
        data["question_index"] = len(questions) - 1
        _restore_selected(data)
        await dialog_manager.switch_to(questions_state)

    async def on_keep_text_answer(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager,
    ) -> None:
        # текстовый вопрос уже отвечен (вернулись «Назад» / обновляем анкету)
        await advance_question(dialog_manager)

    return QuestionnaireHandlers(
        on_multi_select_next=on_multi_select_next,
        on_question_back=on_question_back,
        on_text_answer=on_text_answer,
        on_confirm_back=on_confirm_back,
        on_keep_text_answer=on_keep_text_answer,
    )
