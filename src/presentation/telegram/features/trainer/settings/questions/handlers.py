from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.input import ManagedTextInput

from src.application.mediator import Mediator
from src.application.use_cases.registration_questions.add_custom import (
    AddCustomQuestionRequest,
)
from src.application.use_cases.registration_questions.delete import (
    DeleteCustomQuestionRequest,
)
from src.application.use_cases.registration_questions.update import (
    UpdateQuestionOptionsRequest,
)
from src.application.use_cases.registration_questions.get_by_id import (
    GetRegistrationQuestionByIdRequest,
)
from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.enums.question_type import QuestionType

from .states import TrainerQuestionsSG


async def on_question_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["editing_question_id"] = int(item_id)
    await dialog_manager.switch_to(TrainerQuestionsSG.question_detail)


async def on_add_question_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(TrainerQuestionsSG.add_question)


def is_multi_select_question(data: dict, widget, manager: DialogManager) -> bool:
    return data.get("is_multi_select", False)


def is_deletable_question(data: dict, widget, manager: DialogManager) -> bool:
    return not data.get("is_system", True)


async def on_add_option_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(TrainerQuestionsSG.add_option)


@inject
async def on_remove_option_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    question_id: int = dialog_manager.dialog_data["editing_question_id"]
    question: RegistrationQuestion | None = await mediator.handle(
        GetRegistrationQuestionByIdRequest(question_id=question_id)
    )
    if question is None or not question.options:
        await callback.answer("Нечего удалять")
        return

    if len(question.options) <= 1:
        await callback.answer("Должен остаться хотя бы один вариант", show_alert=True)
        return

    new_options = question.options[:-1]
    await mediator.handle(
        UpdateQuestionOptionsRequest(question_id=question_id, options=new_options)
    )
    await callback.answer("Последний вариант удалён")


@inject
async def on_delete_question_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    question_id: int = dialog_manager.dialog_data["editing_question_id"]
    await mediator.handle(DeleteCustomQuestionRequest(question_id=question_id))
    await callback.answer("Вопрос удалён")
    await dialog_manager.switch_to(TrainerQuestionsSG.main)


@inject
async def on_option_added(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    data: str,
    /,
    mediator: FromDishka[Mediator],
) -> None:
    question_id: int = dialog_manager.dialog_data["editing_question_id"]
    question: RegistrationQuestion | None = await mediator.handle(
        GetRegistrationQuestionByIdRequest(question_id=question_id)
    )
    if question is None:
        await dialog_manager.switch_to(TrainerQuestionsSG.main)
        return

    new_options = [*question.options, data]
    await mediator.handle(
        UpdateQuestionOptionsRequest(question_id=question_id, options=new_options)
    )
    await dialog_manager.switch_to(TrainerQuestionsSG.question_detail)


@inject
async def on_question_added(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    data: str,
    /,
    mediator: FromDishka[Mediator],
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    await mediator.handle(AddCustomQuestionRequest(trainer_id=trainer_id, label=data))
    await dialog_manager.switch_to(TrainerQuestionsSG.main)
