from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from src.presentation.telegram.features.client.booking.states import BookingSG


async def on_booking_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    await dialog_manager.start(
        state=BookingSG.select_day,
        data={"trainer_id": trainer_id},
    )


async def on_stub_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await callback.answer()
    await callback.message.answer(
        "🛠 Этот раздел в разработке — появится в одном из следующих спринтов."
    )
