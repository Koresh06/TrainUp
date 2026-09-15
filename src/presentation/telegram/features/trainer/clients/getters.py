from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.use_cases.client.get_answers_by_id import GetClientAnswersRequest
from src.application.use_cases.client.get_by_id import GetClientByIdRequest
from src.application.use_cases.recurring_booking.get_all_active_by_trainer import (
    GetActiveRecurringBookingsByTrainerRequest,
)
from src.application.use_cases.registration_questions.get_all import (
    GetAllRegistrationQuestionsRequest,
)
from src.domain.entities.client import Client
from src.application.mediator import Mediator
from src.application.use_cases.client.get_clients_by_trainer import (
    GetClientsByTrainerIdRequest,
)
from src.domain.entities.client_answer import ClientAnswer
from src.domain.entities.recurring_booking import RecurringBooking
from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.enums.training import SPORT_EXPERIENCE_LABELS


@inject
async def clients_list_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    clients: list[Client] = await mediator.handle(
        GetClientsByTrainerIdRequest(trainer_id=trainer_id)
    )

    items = [
        {
            "id": str(c.id),
            "label": f"{c.first_name} {c.last_name or ''}".strip() + f" — {c.phone}",
        }
        for c in clients
    ]

    return {"clients": items}


@inject
async def client_detail_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    client_id: int = dialog_manager.dialog_data["viewing_client_id"]
    trainer_id: int = dialog_manager.start_data["trainer_id"]

    client: Client = await mediator.handle(GetClientByIdRequest(client_id=client_id))

    questions: list[RegistrationQuestion] = await mediator.handle(
        GetAllRegistrationQuestionsRequest(trainer_id=trainer_id)
    )
    answers: list[ClientAnswer] = await mediator.handle(
        GetClientAnswersRequest(client_id=client_id)
    )
    answers_by_question = {a.question_id: a.value for a in answers}

    answers_lines = []
    for q in questions:
        value = answers_by_question.get(q.id)
        if value:
            answers_lines.append(f"{q.label}: {', '.join(value)}")
    answers_summary = "\n".join(answers_lines) if answers_lines else "—"

    recurring_list: list[RecurringBooking] = await mediator.handle(
        GetActiveRecurringBookingsByTrainerRequest(trainer_id=trainer_id)
    )
    is_recurring = any(r.client_id == client_id for r in recurring_list)

    return {
        "full_name": f"{client.first_name} {client.last_name or ''}".strip(),
        "phone": client.phone,
        "age": client.age,
        "sport_experience": SPORT_EXPERIENCE_LABELS.get(client.sport_experience, "—"),
        "username": f"@{client.username}" if client.username else "—",
        "answers_summary": answers_summary,
        "recurring_note": "\n🔁 Постоянный клиент" if is_recurring else "",
    }
