from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Select

from src.application.mediator import Mediator
from src.application.use_cases.client.get_by_tg_id import GetClientByTgIdRequest
from src.application.use_cases.client_request.create_consultation import (
    CreateConsultationRequestRequest,
)
from src.domain.entities.client import Client
from src.domain.enums.consultation import ConsultationType

from .states import ClientConsultationSG


async def on_consultation_type_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["consultation_type"] = item_id
    dialog_manager.dialog_data["comment"] = None
    await dialog_manager.switch_to(ClientConsultationSG.comment)


async def on_comment_entered(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    value: str,
) -> None:
    dialog_manager.dialog_data["comment"] = value
    await dialog_manager.switch_to(ClientConsultationSG.confirm)


async def on_comment_skip(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data["comment"] = None
    await dialog_manager.switch_to(ClientConsultationSG.confirm)


@inject
async def on_consultation_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    data = dialog_manager.dialog_data
    client: Client = await mediator.handle(
        GetClientByTgIdRequest(tg_id=callback.from_user.id)
    )

    await mediator.handle(
        CreateConsultationRequestRequest(
            client_id=client.id,
            trainer_id=trainer_id,
            consultation_type=ConsultationType(data["consultation_type"]),
            comment=data.get("comment"),
        )
    )

    await callback.answer(
        "Заявка отправлена! Тренер свяжется с вами в ближайшее время.",
        show_alert=True,
    )
    await dialog_manager.done()
