from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button, Select

from src.application.mediator import Mediator
from src.application.use_cases.trainer_reminder_settings.get_by_trainer_id import (
    GetTrainerReminderSettingsRequest,
)
from src.application.use_cases.trainer_reminder_settings.update import (
    UpdateTrainerReminderSettingsRequest,
)
from src.application.use_cases.trainer_reminder_settings.update_digest import (
    UpdateTrainerDigestSettingsRequest,
)
from src.domain.entities.trainer_reminder_settings import TrainerReminderSettings

from .states import TrainerReminderSettingsSG


@inject
async def on_reminder_hours_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
    /,
    mediator: FromDishka[Mediator],
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    await mediator.handle(
        UpdateTrainerReminderSettingsRequest(
            trainer_id=trainer_id, hours_before=int(item_id)
        )
    )
    await callback.answer("✅ Обновлено")
    await dialog_manager.switch_to(TrainerReminderSettingsSG.main)


async def _update_digest(dialog_manager: DialogManager, mediator: Mediator, **changes) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    current: TrainerReminderSettings = await mediator.handle(
        GetTrainerReminderSettingsRequest(trainer_id=trainer_id)
    )
    values = {
        "morning_digest_hour": current.morning_digest_hour,
        "evening_digest_hour": current.evening_digest_hour,
        "digest_on_empty_days": current.digest_on_empty_days,
        **changes,
    }
    await mediator.handle(UpdateTrainerDigestSettingsRequest(trainer_id=trainer_id, **values))


@inject
async def on_morning_hour_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
    /,
    mediator: FromDishka[Mediator],
) -> None:
    await _update_digest(dialog_manager, mediator, morning_digest_hour=int(item_id))
    await callback.answer("✅ Сохранено")
    await dialog_manager.switch_to(TrainerReminderSettingsSG.main)


@inject
async def on_evening_hour_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
    /,
    mediator: FromDishka[Mediator],
) -> None:
    await _update_digest(dialog_manager, mediator, evening_digest_hour=int(item_id))
    await callback.answer("✅ Сохранено")
    await dialog_manager.switch_to(TrainerReminderSettingsSG.main)


@inject
async def on_morning_off(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    await _update_digest(dialog_manager, mediator, morning_digest_hour=None)
    await dialog_manager.switch_to(TrainerReminderSettingsSG.main)


@inject
async def on_evening_off(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    await _update_digest(dialog_manager, mediator, evening_digest_hour=None)
    await dialog_manager.switch_to(TrainerReminderSettingsSG.main)


@inject
async def on_toggle_empty_days(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    current: TrainerReminderSettings = await mediator.handle(
        GetTrainerReminderSettingsRequest(trainer_id=dialog_manager.start_data["trainer_id"])
    )
    await _update_digest(
        dialog_manager, mediator, digest_on_empty_days=not current.digest_on_empty_days
    )
