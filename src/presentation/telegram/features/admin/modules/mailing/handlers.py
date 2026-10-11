from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Select
from dishka.integrations.aiogram_dialog import inject, FromDishka

from src.application.mediator import Mediator
from src.application.use_cases.mailing.enqueue import EnqueueMailingRequest
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdRequest
from src.domain.entities.trainer import Trainer
from src.domain.enums.mailing import MailingTarget
from src.presentation.telegram.features.admin.states import AdminMailingSG

from .getters import mailing_param


async def on_mailing_target_selected(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    target = MailingTarget(button.widget_id)
    dialog_manager.dialog_data["target"] = target.value
    dialog_manager.dialog_data["trainer_id"] = None
    if target == MailingTarget.TRAINER_CLIENTS:
        await dialog_manager.switch_to(AdminMailingSG.select_trainer)
    else:
        await dialog_manager.switch_to(AdminMailingSG.compose)


@inject
async def on_mailing_trainer_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
    mediator: FromDishka[Mediator],
) -> None:
    trainer: Trainer = await mediator.handle(GetTrainerByIdRequest(trainer_id=int(item_id)))
    dialog_manager.dialog_data["trainer_id"] = trainer.id
    dialog_manager.dialog_data["trainer_name"] = trainer.name
    await dialog_manager.switch_to(AdminMailingSG.compose)


async def on_mailing_message_received(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data["from_chat_id"] = message.chat.id
    dialog_manager.dialog_data["message_id"] = message.message_id
    # предпросмотр — ровно то, что получат пользователи
    await message.bot.copy_message(
        chat_id=message.chat.id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )
    await dialog_manager.switch_to(AdminMailingSG.confirm)


@inject
async def on_mailing_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    await mediator.handle(
        EnqueueMailingRequest(
            target=MailingTarget(mailing_param(dialog_manager, "target")),
            from_chat_id=dialog_manager.dialog_data["from_chat_id"],
            message_id=dialog_manager.dialog_data["message_id"],
            trainer_id=mailing_param(dialog_manager, "trainer_id"),
        )
    )
    await callback.answer(
        "🚀 Рассылка запущена! Отчёт придёт по завершении.", show_alert=True
    )
    await dialog_manager.done()
