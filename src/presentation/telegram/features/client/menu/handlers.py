from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from src.presentation.telegram.features.client.booking.states import BookingSG
from src.presentation.telegram.features.client.consultation.states import (
    ClientConsultationSG,
)
from src.presentation.telegram.features.client.feedback.states import ClientFeedbackSG
from src.presentation.telegram.features.client.menu.states import ClientMenuSG
from src.presentation.telegram.features.client.profile.states import ClientProfileSG
from src.presentation.telegram.features.client.program.states import ClientProgramSG

CLIENT_MENU_TARGETS = {
    "booking": BookingSG.select_day,
    "program": ClientProgramSG.program_type,
    "consultation": ClientConsultationSG.consultation_type,
    "feedback": ClientFeedbackSG.main,
    "profile": ClientProfileSG.main,
}


async def on_menu_item_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    await dialog_manager.start(
        state=CLIENT_MENU_TARGETS[button.widget_id],
        data={"trainer_id": trainer_id},
    )


async def on_trainer_profile_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(ClientMenuSG.trainer_profile)


async def on_my_bookings_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.switch_to(ClientMenuSG.my_bookings)
