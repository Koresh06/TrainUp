from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.input import ManagedTextInput

from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.exception.client import AssigningClientToAnotherTrainerError
from src.application.mediator import Mediator
from src.application.use_cases.client.register import RegisterClientRequest
from src.application.use_cases.registration_questions.get_active import (
    GetActiveRegistrationQuestionsRequest,
)
from src.presentation.telegram.features.client.menu.states import ClientMenuSG
from src.presentation.telegram.features.client.questionnaire import (
    load_questions,
    make_questionnaire_handlers,
)

from .states import ClientRegisterSG


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

    load_questions(dialog_manager.dialog_data, questions)

    if not questions:
        await dialog_manager.switch_to(ClientRegisterSG.confirm)
    else:
        await dialog_manager.switch_to(ClientRegisterSG.questions)


_questionnaire = make_questionnaire_handlers(
    questions_state=ClientRegisterSG.questions,
    done_state=ClientRegisterSG.confirm,
    exit_state=ClientRegisterSG.sport_experience,
)
on_multi_select_next = _questionnaire.on_multi_select_next
on_question_back = _questionnaire.on_question_back
on_text_answer = _questionnaire.on_text_answer
on_confirm_back = _questionnaire.on_confirm_back
on_keep_text_answer = _questionnaire.on_keep_text_answer


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
