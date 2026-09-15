from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button

from .helper import ScopePrivate


async def on_period_selected(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data["period_trainer"] = button.widget_id
    await dialog_manager.show(show_mode=ShowMode.EDIT)