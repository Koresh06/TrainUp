from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput

from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.enums.question_type import QuestionType
from src.domain.exception.client import AssigningClientToAnotherTrainerError
from src.application.mediator import Mediator
from src.application.use_cases.client.register import RegisterClientRequest
from src.application.use_cases.registration_questions.get_active import (
    GetActiveRegistrationQuestionsRequest,
)
from src.presentation.telegram.features.client.menu.states import ClientMenuSG

from .states import ClientRegisterSG
from .helpers import _current_question, _restore_selected


async def on_full_name_success(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: tuple[str, str | None],
) -> None:
    (
        dialog_manager.dialog_data["first_name"],
        dialog_manager.dialog_data["last_name"],
    ) = data
    await dialog_manager.switch_to(ClientRegisterSG.age)


@inject
async def on_age_input_success(
    message: Message,
    widget: ManagedTextInput[int],
    dialog_manager: DialogManager,
    value: int,
) -> None:
    dialog_manager.dialog_data["age"] = value
    await dialog_manager.next()


@inject
async def on_phone_received_contact(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
) -> None:
    new_phone = message.contact.phone_number
    if not new_phone.startswith("+"):
        new_phone = f"+{new_phone}"
    dialog_manager.dialog_data["phone"] = new_phone
    await dialog_manager.next()


@inject
async def on_phone_input_success(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    value: str,
) -> None:
    dialog_manager.dialog_data["phone"] = value.strip()
    await dialog_manager.next()


@inject
async def on_sport_experience_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
    mediator: FromDishka[Mediator],
) -> None:
    dialog_manager.dialog_data["sport_experience"] = item_id

    trainer_id: int = dialog_manager.start_data["trainer_id"]
    questions: list[RegistrationQuestion] = await mediator.handle(
        GetActiveRegistrationQuestionsRequest(trainer_id=trainer_id)
    )

    dialog_manager.dialog_data["questions"] = [
        {
            "id": q.id,
            "type": q.question_type.value,
            "label": q.label,
            "options": q.options,
        }
        for q in questions
    ]
    dialog_manager.dialog_data["question_index"] = 0
    dialog_manager.dialog_data["answers"] = {}  # question_id (str) -> list[str]
    dialog_manager.dialog_data["current_selected"] = (
        []
    )  # индексы выбранных опций текущего MULTI_SELECT

    if not questions:
        await dialog_manager.switch_to(ClientRegisterSG.confirm)
    else:
        await dialog_manager.switch_to(ClientRegisterSG.questions)


async def on_option_toggle(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    index = int(item_id)
    selected: list[int] = dialog_manager.dialog_data.setdefault("current_selected", [])
    if index in selected:
        selected.remove(index)
    else:
        selected.append(index)


async def _advance_question(dialog_manager: DialogManager) -> None:
    dialog_manager.dialog_data["question_index"] += 1
    dialog_manager.dialog_data["current_selected"] = []

    if _current_question(dialog_manager.dialog_data) is None:
        await dialog_manager.switch_to(ClientRegisterSG.confirm)
    else:
        await dialog_manager.switch_to(ClientRegisterSG.questions)


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

    values = [question["options"][i] for i in selected]
    data["answers"][str(question["id"])] = values

    await _advance_question(dialog_manager)


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
        await dialog_manager.switch_to(ClientRegisterSG.questions)
    else:
        await dialog_manager.back()


async def on_text_answer(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
) -> None:
    data = dialog_manager.dialog_data
    question = _current_question(data)
    if question is None or question["type"] != QuestionType.TEXT.value:
        return

    text = (message.text or "").strip()
    if not text:
        await message.answer("Введите текст ответа")
        return

    data["answers"][str(question["id"])] = [text]

    await _advance_question(dialog_manager)


@inject
async def on_register_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    data = dialog_manager.dialog_data
    user = callback.from_user

    try:
        await mediator.handle(
            RegisterClientRequest(
                tg_id=user.id,
                trainer_id=trainer_id,
                first_name=data["first_name"],
                last_name=data.get("last_name"),
                username=user.username,
                phone=data["phone"],
                age=data["age"],
                sport_experience=data["sport_experience"],
                answers=data.get("answers", {}),
            )
        )
    except AssigningClientToAnotherTrainerError:
        await callback.answer(
            "Вы уже зарегистрированы у другого тренера в этом боте",
            show_alert=True,
        )
        return

    await dialog_manager.start(
        ClientMenuSG.main,
        mode=StartMode.RESET_STACK,
        data={"trainer_id": trainer_id},
    )
