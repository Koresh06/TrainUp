from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput

from src.application.mediator import Mediator
from src.application.use_cases.trainer.update import UpdateTrainerProfileRequest

from src.presentation.telegram.features.trainer.register.states import SubscriptionSG

from .states import TrainerProfileSG


async def on_renew_subscription_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.start(
        state=SubscriptionSG.select_plan,
        mode=StartMode.RESET_STACK,
        data={"trainer_id": dialog_manager.start_data["trainer_id"]},
    )


async def on_profile_edit_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    target = {
        "edit_photo": TrainerProfileSG.photo,
        "edit_social_links": TrainerProfileSG.social_links,
    }[button.widget_id]
    await dialog_manager.switch_to(target)


@inject
async def on_photo_received(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    if not message.photo:
        await message.answer("Пожалуйста, отправьте фото")
        return

    trainer_id: int = dialog_manager.start_data["trainer_id"]
    file_id = message.photo[-1].file_id
    await mediator.handle(
        UpdateTrainerProfileRequest(trainer_id=trainer_id, photo_file_id=file_id)
    )
    await dialog_manager.switch_to(TrainerProfileSG.main)


@inject
async def on_social_links_success(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: dict[str, str],
    mediator: FromDishka[Mediator],
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    await mediator.handle(
        UpdateTrainerProfileRequest(trainer_id=trainer_id, social_links=data)
    )
    await dialog_manager.switch_to(TrainerProfileSG.main)
