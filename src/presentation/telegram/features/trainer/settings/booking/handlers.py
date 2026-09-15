from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Select
from aiogram_dialog.widgets.kbd.select import OnItemClick

from src.application.mediator import Mediator
from src.application.use_cases.trainer_booking_settings.get_by_id import (
    GetTrainerBookingSettingsRequest,
)
from src.application.use_cases.trainer_booking_settings.update import (
    UpdateTrainerBookingSettingsRequest,
)
from src.domain.entities.trainer_booking_settings import TrainerBookingSettings
from src.presentation.telegram.features.trainer.settings.booking.states import (
    TrainerBookingSettingsSG,
)


@inject
async def on_horizon_weeks_selected(
    callback: CallbackQuery,
    widget: OnItemClick[Select[str], str],
    dialog_manager: DialogManager,
    item_id: str,
    /,
    mediator: FromDishka[Mediator],
) -> None:
    weeks = int(item_id)
    horizon_days = weeks * 7

    trainer_id: int = dialog_manager.start_data["trainer_id"]
    current: TrainerBookingSettings = await mediator.handle(
        GetTrainerBookingSettingsRequest(trainer_id=trainer_id)
    )

    await mediator.handle(
        UpdateTrainerBookingSettingsRequest(
            trainer_id=trainer_id,
            calendar_horizon_days=horizon_days,
            max_active_bookings_per_client=current.max_active_bookings_per_client,
        )
    )
    await callback.answer(f"✅ Горизонт календаря обновлён: {weeks} нед.")
    await dialog_manager.switch_to(TrainerBookingSettingsSG.main)


@inject
async def on_max_bookings_entered(
    message: Message,
    widget: ManagedTextInput[int],
    dialog_manager: DialogManager,
    value: int,
    mediator: FromDishka[Mediator],
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    current: TrainerBookingSettings = await mediator.handle(
        GetTrainerBookingSettingsRequest(trainer_id=trainer_id)
    )

    await mediator.handle(
        UpdateTrainerBookingSettingsRequest(
            trainer_id=trainer_id,
            calendar_horizon_days=current.calendar_horizon_days,
            max_active_bookings_per_client=value,
        )
    )
    await message.answer(f"✅ Лимит записей обновлён: {value}")
    await dialog_manager.switch_to(TrainerBookingSettingsSG.main)
