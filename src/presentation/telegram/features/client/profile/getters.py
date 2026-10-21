from html import escape

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.client.get_answers_by_id import GetClientAnswersRequest
from src.application.use_cases.client.get_by_tg_id import GetClientByTgIdRequest
from src.application.use_cases.registration_questions.get_all import (
    GetAllRegistrationQuestionsRequest,
)
from src.domain.entities.client import Client
from src.domain.entities.client_answer import ClientAnswer
from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.enums.training import SPORT_EXPERIENCE_LABELS


@inject
async def client_profile_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    client: Client = await mediator.handle(
        GetClientByTgIdRequest(tg_id=dialog_manager.event.from_user.id)
    )
    questions: list[RegistrationQuestion] = await mediator.handle(
        GetAllRegistrationQuestionsRequest(trainer_id=trainer_id)
    )
    answers: list[ClientAnswer] = await mediator.handle(
        GetClientAnswersRequest(client_id=client.id)
    )
    answers_by_question = {a.question_id: a.value for a in answers}

    lines = [
        f"<b>{escape(q.label)}</b>\n{escape(', '.join(answers_by_question[q.id]))}"
        for q in questions
        if answers_by_question.get(q.id)
    ]

    return {
        "full_name": escape(f"{client.first_name} {client.last_name or ''}".strip()),
        "phone": client.phone or "—",
        "age": f"{client.age} лет" if client.age else "—",
        "sport_experience": SPORT_EXPERIENCE_LABELS.get(client.sport_experience, "—"),
        "answers_summary": "\n\n".join(lines) if lines else "Ответов пока нет.",
    }


async def answers_confirm_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    data = dialog_manager.dialog_data
    questions: list[dict] = data.get("questions", [])
    answers: dict[str, list[str]] = data.get("answers", {})

    lines = [
        f"<b>{escape(q['label'])}</b>\n{escape(', '.join(answers[str(q['id'])]))}"
        for q in questions
        if answers.get(str(q["id"]))
    ]
    return {"answers_summary": "\n\n".join(lines) if lines else "—"}
