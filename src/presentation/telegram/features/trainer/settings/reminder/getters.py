from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.trainer_reminder_settings.get_by_trainer_id import (
    GetTrainerReminderSettingsRequest,
)
from src.domain.entities.trainer_reminder_settings import TrainerReminderSettings
from src.domain.constants import REMINDER_HOUR_OPTIONS


@inject
async def reminder_settings_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    settings: TrainerReminderSettings = await mediator.handle(
        GetTrainerReminderSettingsRequest(trainer_id=trainer_id)
    )
    return {"hours_before": settings.hours_before}


@inject
async def reminder_hours_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    settings: TrainerReminderSettings = await mediator.handle(
        GetTrainerReminderSettingsRequest(trainer_id=trainer_id)
    )
    return {
        "hours": [
            {
                "id": str(h),
                "label": f"{'✅ ' if h == settings.hours_before else ''}{h} ч.",
            }
            for h in REMINDER_HOUR_OPTIONS
        ]
    }
