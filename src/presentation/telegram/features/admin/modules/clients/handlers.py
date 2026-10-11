from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, Select
from dishka.integrations.aiogram_dialog import inject, FromDishka

from src.application.mediator import Mediator
from src.application.use_cases.client.get_by_id import GetClientByIdRequest
from src.application.use_cases.client.set_blocked import SetClientBlockedRequest
from src.domain.entities.client import Client
from src.presentation.telegram.features.admin.states import AdminClientsSG


def validate_clients_query(value: str) -> str:
    value = value.strip()
    if not 2 <= len(value) <= 64:
        raise ValueError("Введите от 2 до 64 символов")
    return value


async def on_clients_query_entered(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    value: str,
) -> None:
    dialog_manager.dialog_data["clients_query"] = value
    await dialog_manager.switch_to(AdminClientsSG.list)


async def on_recent_clients_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data["clients_query"] = ""
    await dialog_manager.switch_to(AdminClientsSG.list)


async def on_client_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["client_id"] = int(item_id)
    await dialog_manager.switch_to(AdminClientsSG.card)


@inject
async def on_toggle_client_block(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    client: Client = await mediator.handle(
        GetClientByIdRequest(client_id=dialog_manager.dialog_data["client_id"])
    )
    await mediator.handle(SetClientBlockedRequest(client_id=client.id, blocked=client.is_active))
    await callback.answer("⛔ Заблокирован" if client.is_active else "✅ Разблокирован")
