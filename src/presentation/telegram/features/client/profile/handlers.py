from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from src.application.mediator import Mediator
from src.application.use_cases.client.get_answers_by_id import GetClientAnswersRequest
from src.application.use_cases.client.get_by_tg_id import GetClientByTgIdRequest
from src.application.use_cases.client.update_answers import UpdateClientAnswersRequest
from src.application.use_cases.registration_questions.get_active import (
    GetActiveRegistrationQuestionsRequest,
)
from src.domain.entities.client import Client
from src.domain.entities.client_answer import ClientAnswer
from src.domain.entities.registration_question import RegistrationQuestion
from src.presentation.telegram.features.client.questionnaire import (
    load_questions,
    make_questionnaire_handlers,
)

from .states import ClientProfileSG


@inject
async def on_edit_answers_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    questions: list[RegistrationQuestion] = await mediator.handle(
        GetActiveRegistrationQuestionsRequest(trainer_id=trainer_id)
    )
    if not questions:
        await callback.answer("Тренер пока не добавил вопросов анкеты", show_alert=True)
        return

    client: Client = await mediator.handle(
        GetClientByTgIdRequest(tg_id=callback.from_user.id)
    )
    current: list[ClientAnswer] = await mediator.handle(
        GetClientAnswersRequest(client_id=client.id)
    )
    # текущие ответы подставляем как выбранные — клиенту достаточно поправить нужное
    load_questions(
        dialog_manager.dialog_data,
        questions,
        answers={str(a.question_id): a.value for a in current},
    )
    await dialog_manager.switch_to(ClientProfileSG.questions)


@inject
async def on_answers_save(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    client: Client = await mediator.handle(
        GetClientByTgIdRequest(tg_id=callback.from_user.id)
    )
    active_ids = {str(q["id"]) for q in dialog_manager.dialog_data["questions"]}
    answers = {
        qid: value
        for qid, value in dialog_manager.dialog_data["answers"].items()
        if qid in active_ids and value
    }
    await mediator.handle(UpdateClientAnswersRequest(client_id=client.id, answers=answers))
    await callback.answer("✅ Анкета обновлена — тренер увидит новые ответы")
    await dialog_manager.switch_to(ClientProfileSG.main)


_questionnaire = make_questionnaire_handlers(
    questions_state=ClientProfileSG.questions,
    done_state=ClientProfileSG.confirm,
    exit_state=ClientProfileSG.main,
)
on_multi_select_next = _questionnaire.on_multi_select_next
on_question_back = _questionnaire.on_question_back
on_text_answer = _questionnaire.on_text_answer
on_confirm_back = _questionnaire.on_confirm_back
on_keep_text_answer = _questionnaire.on_keep_text_answer
