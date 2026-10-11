from html import escape

from aiogram_dialog import DialogManager

from src.domain.constants import PROGRAM_TYPE_LABELS, TRAINING_DIRECTION_LABELS
from src.domain.enums.program import ProgramType
from src.domain.enums.training import TrainingDirection


async def program_types_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    return {
        "program_types": [
            {"id": t.value, "label": label} for t, label in PROGRAM_TYPE_LABELS.items()
        ]
    }


async def directions_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    return {
        "directions": [
            {"id": d.value, "label": label}
            for d, label in TRAINING_DIRECTION_LABELS.items()
        ]
    }


async def comment_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    direction = TrainingDirection(dialog_manager.dialog_data["direction"])
    is_custom_goal = direction == TrainingDirection.CUSTOM_GOAL
    return {
        "comment_hint": (
            "Опишите вашу цель — чего хотите добиться?"
            if is_custom_goal
            else "Добавьте комментарий для тренера (пожелания, удобные дни, "
            "ограничения по здоровью) или пропустите этот шаг."
        ),
        # для «конкретной цели» комментарий обязателен
        "can_skip": not is_custom_goal,
    }


async def program_confirm_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    data = dialog_manager.dialog_data
    comment = data.get("comment")
    return {
        "program_type": PROGRAM_TYPE_LABELS[ProgramType(data["program_type"])],
        "direction": TRAINING_DIRECTION_LABELS[TrainingDirection(data["direction"])],
        "comment": escape(comment) if comment else "—",
    }
