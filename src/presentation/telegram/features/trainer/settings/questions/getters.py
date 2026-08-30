from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, Select

from src.application.mediator import Mediator
from src.application.use_cases.registration_questions.get_all import (
    GetAllRegistrationQuestionsRequest,
)
from src.application.use_cases.registration_questions.get_by_id import (
    GetRegistrationQuestionByIdRequest,
)
from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.enums.question_type import QuestionType


@inject
async def questions_list_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    questions: list[RegistrationQuestion] = await mediator.handle(
        GetAllRegistrationQuestionsRequest(trainer_id=trainer_id)
    )
    return {
        "questions": [
            {
                "id": str(q.id),
                "label": f"{'🔒 ' if q.is_system else ''}{q.label}",
            }
            for q in questions
        ]
    }


@inject
async def question_detail_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    question_id: int = dialog_manager.dialog_data["editing_question_id"]
    question: RegistrationQuestion | None = await mediator.handle(
        GetRegistrationQuestionByIdRequest(question_id=question_id)
    )
    if question is None:
        return {
            "label": "Вопрос не найден",
            "options_summary": "",
            "is_multi_select": False,
            "is_system": True,
        }

    options_summary = "\n".join(f"• {opt}" for opt in question.options) or "—"

    return {
        "label": question.label,
        "options_summary": options_summary,
        "is_multi_select": question.question_type == QuestionType.MULTI_SELECT,
        "is_system": question.is_system,
    }
