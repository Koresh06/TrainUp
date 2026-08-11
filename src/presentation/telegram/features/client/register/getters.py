from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdRequest

from src.domain.entities.trainer import Trainer
from src.domain.enums.training import TrainingDirection


@inject
async def welcome_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    trainer: Trainer = await mediator.handle(GetTrainerByIdRequest(trainer_id=trainer_id))
    return {"trainer_name": trainer.name, "trainer_bio": trainer.bio}

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


@inject
async def register_confirm_getter(
    dialog_manager: DialogManager,
    **kwargs,
) -> dict:
    data = dialog_manager.dialog_data
    return {
        "phone": data.get("phone"),
        "age": data.get("age"),
        "goals": ", ".join(data.get("goals", [])) or "не указано",
        "health_notes": data.get("health_notes") or "не указано",
        "injuries": data.get("injuries") or "не указано",
    }
