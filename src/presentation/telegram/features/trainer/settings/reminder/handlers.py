from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Select

from src.application.mediator import Mediator
from src.application.use_cases.trainer_reminder_settings.update import (
    UpdateTrainerReminderSettingsRequest,
)


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
    await dialog_manager.back()