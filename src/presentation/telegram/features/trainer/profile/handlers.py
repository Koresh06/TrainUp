import logging

from aiogram.exceptions import TelegramAPIError
from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput

from src.application.mediator import Mediator
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdRequest
from src.application.use_cases.trainer.update import UpdateTrainerProfileRequest
from src.domain.entities.trainer import Trainer
from src.presentation.telegram.features.trainer.register.states import SubscriptionSG

from .states import TrainerProfileSG

logger = logging.getLogger(__name__)

GROUP_TEST_TEXT = (
    "✅ <b>TrainUp на связи</b>\n\n"
    "Сюда будут приходить новые записи, отмены и заявки клиентов."
)


async def _update(dialog_manager: DialogManager, mediator: Mediator, **changes) -> None:
    await mediator.handle(
        UpdateTrainerProfileRequest(trainer_id=dialog_manager.start_data["trainer_id"], **changes)
    )
    await dialog_manager.switch_to(TrainerProfileSG.main)


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


@inject
async def on_name_input(
    message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, value: str,
    mediator: FromDishka[Mediator],
) -> None:
    await _update(dialog_manager, mediator, name=value)


@inject
async def on_bio_input(
    message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, value: str,
    mediator: FromDishka[Mediator],
) -> None:
    await _update(dialog_manager, mediator, bio=value)


@inject
async def on_bio_clear(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    await _update(dialog_manager, mediator, bio="")


@inject
async def on_phone_input(
    message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, value: str,
    mediator: FromDishka[Mediator],
) -> None:
    await _update(dialog_manager, mediator, phone=value)


@inject
async def on_phone_contact(
    message: Message, widget: MessageInput, dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    phone = message.contact.phone_number
    await _update(dialog_manager, mediator, phone=phone if phone.startswith("+") else f"+{phone}")


@inject
async def on_photo_received(
    message: Message, widget: MessageInput, dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    if not message.photo:
        await message.answer("Пожалуйста, отправьте фото")
        return
    await _update(dialog_manager, mediator, photo_file_id=message.photo[-1].file_id)


@inject
async def on_photo_remove(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    await _update(dialog_manager, mediator, remove_photo=True)


@inject
async def on_social_links_success(
    message: Message, widget: ManagedTextInput, dialog_manager: DialogManager,
    data: dict[str, str], mediator: FromDishka[Mediator],
) -> None:
    await _update(dialog_manager, mediator, social_links=data)


@inject
async def on_social_links_clear(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    await _update(dialog_manager, mediator, social_links={})


async def _set_group(message: Message, dialog_manager: DialogManager, mediator: Mediator, chat_id: int) -> None:
    # сначала проверяем, что бот реально может писать в новую группу —
    # иначе тренер «сменит» группу и перестанет получать записи
    try:
        await message.bot.send_message(chat_id, GROUP_TEST_TEXT)
    except TelegramAPIError as error:
        logger.warning("[TrainerProfile] cannot post to new group %s: %s", chat_id, error)
        await message.answer(
            "❌ Бот не может писать в эту группу. Проверьте, что он добавлен "
            "администратором с правом публикации, и выберите её ещё раз."
        )
        return
    await _update(dialog_manager, mediator, notification_chat_id=chat_id)


@inject
async def on_group_shared(
    message: Message, widget: MessageInput, dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    await _set_group(message, dialog_manager, mediator, message.chat_shared.chat_id)


@inject
async def on_group_test(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    trainer: Trainer = await mediator.handle(
        GetTrainerByIdRequest(trainer_id=dialog_manager.start_data["trainer_id"])
    )
    try:
        await callback.bot.send_message(trainer.notification_chat_id, GROUP_TEST_TEXT)
    except TelegramAPIError as error:
        logger.warning("[TrainerProfile] test message failed chat=%s: %s", trainer.notification_chat_id, error)
        await callback.answer("❌ Не дошло — выберите группу заново", show_alert=True)
        return
    await callback.answer("✅ Проверочное сообщение отправлено в группу", show_alert=True)
