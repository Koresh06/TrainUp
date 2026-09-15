from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdRequest

from src.domain.entities.trainer import Trainer
from src.domain.enums.question_type import QuestionType
from src.domain.enums.training import (
    SPORT_EXPERIENCE_LABELS,
    SportExperience,
)
from .helpers import _current_question


@inject
async def welcome_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    trainer: Trainer = await mediator.handle(
        GetTrainerByIdRequest(trainer_id=trainer_id)
    )
    return {"trainer_name": trainer.name, "trainer_bio": trainer.bio}


async def sport_experience_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    return {
        "sport_experience_options": [
            {"id": exp.value, "label": label}
            for exp, label in SPORT_EXPERIENCE_LABELS.items()
        ]
    }


async def questions_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    data = dialog_manager.dialog_data
    question = _current_question(data)

    if question is None:
        return {
            "question_label": "",
            "question_type": "",
            "options": [],
            "progress_label": "",
        }

    selected: list[int] = data.get("current_selected", [])
    options = [
        {"id": str(i), "label": f"{'✅' if i in selected else '⬜'} {opt}"}
        for i, opt in enumerate(question["options"])
    ]

    return {
        "question_label": question["label"],
        "question_type": question["type"],
        "options": options,
    }


def is_multi_select(data: dict, widget, manager: DialogManager) -> bool:
    return data.get("question_type") == QuestionType.MULTI_SELECT.value


async def register_confirm_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    data = dialog_manager.dialog_data
    full_name = f"{data.get('first_name', '')} {data.get('last_name') or ''}".strip()

    sport_experience_label = SPORT_EXPERIENCE_LABELS.get(
        SportExperience(data.get("sport_experience")), "—"
    )

    questions: list[dict] = data.get("questions", [])
    answers: dict[str, list[str]] = data.get("answers", {})

    lines = []
    for q in questions:
        value = answers.get(str(q["id"]))
        if value:
            lines.append(f"{q['label']}: {', '.join(value)}")
    answers_summary = "\n".join(lines) if lines else "—"

    return {
        "full_name": full_name,
        "phone": data.get("phone"),
        "age": data.get("age"),
        "sport_experience": sport_experience_label,
        "answers_summary": answers_summary,
    }
