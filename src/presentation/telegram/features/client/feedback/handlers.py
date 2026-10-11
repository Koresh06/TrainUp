from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Select

from src.application.mediator import Mediator
from src.application.use_cases.client.get_by_tg_id import GetClientByTgIdRequest
from src.application.use_cases.client_request.create_feedback import (
    CreateFeedbackRequest,
)
from src.domain.entities.client import Client

from .states import ClientFeedbackSG


async def _send_feedback(
    dialog_manager: DialogManager,
    mediator: Mediator,
    tg_id: int,
    *,
    phone: str | None = None,
    message: str | None = None,
) -> None:
    client: Client = await mediator.handle(GetClientByTgIdRequest(tg_id=tg_id))
    await mediator.handle(
        CreateFeedbackRequest(
            client_id=client.id,
            trainer_id=dialog_manager.start_data["trainer_id"],
            phone=phone,
            message=message,
        )
    )


@inject
async def on_callback_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    client: Client = await mediator.handle(
        GetClientByTgIdRequest(tg_id=callback.from_user.id)
    )
    await _send_feedback(
        dialog_manager, mediator, callback.from_user.id, phone=client.phone
    )
    await callback.answer("Тренер перезвонит вам в ближайшее время 📞", show_alert=True)
    await dialog_manager.done()


@inject
async def on_callback_phone_entered(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    value: str,
    mediator: FromDishka[Mediator],
) -> None:
    await _send_feedback(dialog_manager, mediator, message.from_user.id, phone=value)
    await message.answer("✅ Тренер перезвонит вам в ближайшее время 📞")
    await dialog_manager.done()


@inject
async def on_feedback_message_entered(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    value: str,
    mediator: FromDishka[Mediator],
) -> None:
    await _send_feedback(dialog_manager, mediator, message.from_user.id, message=value)
    await message.answer("✅ Сообщение отправлено тренеру")
    await dialog_manager.done()


async def on_faq_item_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["faq_id"] = int(item_id)
    await dialog_manager.switch_to(ClientFeedbackSG.faq_answer)
