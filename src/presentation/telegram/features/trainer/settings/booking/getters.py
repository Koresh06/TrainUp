from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.trainer_booking_settings.get_by_id import (
    GetTrainerBookingSettingsRequest,
)
from src.domain.entities.trainer_booking_settings import TrainerBookingSettings

WEEK_OPTIONS = list(range(1, 9))  # [1, 2, 3, 4, 5, 6, 7, 8]


@inject
async def booking_settings_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    settings: TrainerBookingSettings = await mediator.handle(
        GetTrainerBookingSettingsRequest(trainer_id=trainer_id)
    )
    horizon_weeks = max(1, round(settings.calendar_horizon_days / 7))
    return {
        "horizon_weeks": horizon_weeks,
        "max_bookings": settings.max_active_bookings_per_client,
    }


@inject
async def horizon_weeks_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    current: TrainerBookingSettings = await mediator.handle(
        GetTrainerBookingSettingsRequest(trainer_id=trainer_id)
    )
    current_weeks = max(1, round(current.calendar_horizon_days / 7))

    return {
        "weeks": [
            {"id": str(w), "label": f"{'✅ ' if w == current_weeks else ''}{w} нед."}
            for w in WEEK_OPTIONS
        ]
    }
