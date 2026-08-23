from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.trainer_booking_settings.get_by_id import (
    GetTrainerBookingSettingsRequest,
)
from src.domain.entities.trainer_booking_settings import TrainerBookingSettings


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
    return {
        "horizon_days": settings.calendar_horizon_days,
        "max_bookings": settings.max_active_bookings_per_client,
    }
