from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdRequest

from src.domain.entities.trainer import Trainer
from src.domain.enums.training import HealthCondition, SportExperience, TrainingDirection


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


SPORT_EXPERIENCE_LABELS: dict[SportExperience, str] = {
    SportExperience.NONE: "Нет опыта",
    SportExperience.UP_TO_3_MONTHS: "До 3 месяцев",
    SportExperience.UP_TO_6_MONTHS: "До 6 месяцев",
    SportExperience.MORE_THAN_YEAR: "Более 1 года",
}


async def sport_experience_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    return {
        "sport_experience_options": [
            {"id": exp.value, "label": label}
            for exp, label in SPORT_EXPERIENCE_LABELS.items()
        ]
    }

HEALTH_CONDITION_LABELS: dict[HealthCondition, str] = {
    HealthCondition.HEALTHY: "Полностью здоров(-а)",
    HealthCondition.HEART: "Проблемы с сердцем",
    HealthCondition.BACK: "Проблемы со спиной",
    HealthCondition.JOINTS: "Проблемы с суставами",
    HealthCondition.OVERWEIGHT: "Избыточный вес",
    HealthCondition.UNDERWEIGHT: "Недостаточный вес",
    HealthCondition.OTHER: "Другое",
}


async def health_conditions_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    return {
        "health_conditions_options": [
            {"id": cond.value, "label": label}
            for cond, label in HEALTH_CONDITION_LABELS.items()
        ]
    }


GOAL_LABELS: dict[TrainingDirection, str] = {
    TrainingDirection.STRENGTH: "Силовые",
    TrainingDirection.CARDIO: "Кардио",
    TrainingDirection.ENDURANCE: "Выносливость",
    TrainingDirection.OFP: "ОФП",
    TrainingDirection.WEIGHT_LOSS: "Снижение веса",
    TrainingDirection.CUSTOM_GOAL: "Своя цель",
}


async def goals_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    return {
        "goals": [
            {"id": direction.value, "label": label}
            for direction, label in GOAL_LABELS.items()
        ]
    }

async def register_confirm_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    data = dialog_manager.dialog_data
    full_name = f"{data.get('first_name', '')} {data.get('last_name') or ''}".strip()

    sport_experience_label = SPORT_EXPERIENCE_LABELS.get(
        SportExperience(data.get("sport_experience")), "—"
    )

    health_conditions_labels = ", ".join(
        HEALTH_CONDITION_LABELS[HealthCondition(c)]
        for c in data.get("health_conditions", [])
    )
    if data.get("health_conditions_other_text"):
        health_conditions_labels += f" ({data['health_conditions_other_text']})"

    goals_labels = ", ".join(
        GOAL_LABELS[TrainingDirection(g)] for g in data.get("goals", [])
    )

    return {
        "full_name": full_name,
        "phone": data.get("phone"),
        "age": data.get("age"),
        "sport_experience": sport_experience_label,
        "health_conditions": health_conditions_labels or "—",
        "goals": goals_labels,
        "health_notes": data.get("health_notes") or "—",
        "injuries": data.get("injuries") or "—",
    }