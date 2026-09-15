from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Select

from .states import TrainerClientsSG


async def on_client_item_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["viewing_client_id"] = int(item_id)
    await dialog_manager.switch_to(TrainerClientsSG.detail)
