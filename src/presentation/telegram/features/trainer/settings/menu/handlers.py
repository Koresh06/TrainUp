from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from .constants import TRAINER_SETTINGS_TARGETS

async def on_settings_item_click(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    widget_id = widget.widget_id
    if widget_id in TRAINER_SETTINGS_TARGETS:
        await dialog_manager.start(
            state=TRAINER_SETTINGS_TARGETS[widget_id],
            data={"trainer_id": trainer_id},
        )
