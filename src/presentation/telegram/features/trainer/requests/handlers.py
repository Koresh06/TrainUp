from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, Select

from src.application.mediator import Mediator
from src.application.use_cases.client_request.update_status import (
    UpdateClientRequestStatusRequest,
)
from src.domain.constants import REQUEST_STATUS_LABELS
from src.domain.enums.request import RequestStatus

from .constants import unpack_request_item_id
from .states import TrainerRequestsSG


async def on_filter_selected(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data["requests_filter"] = button.widget_id


async def on_request_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["request_item_id"] = item_id
    await dialog_manager.switch_to(TrainerRequestsSG.detail)


def can_take(data: dict, widget, manager: DialogManager) -> bool:
    return data.get("can_take", False)


def can_close(data: dict, widget, manager: DialogManager) -> bool:
    return data.get("can_close", False)


def can_reopen(data: dict, widget, manager: DialogManager) -> bool:
    return data.get("can_reopen", False)


REQUEST_STATUS_BUTTONS: dict[str, RequestStatus] = {
    "take_request": RequestStatus.IN_PROGRESS,
    "close_request": RequestStatus.DONE,
    "reopen_request": RequestStatus.IN_PROGRESS,
}


@inject
async def on_change_status_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    kind, request_id = unpack_request_item_id(dialog_manager.dialog_data["request_item_id"])
    status = REQUEST_STATUS_BUTTONS[button.widget_id]
    await mediator.handle(
        UpdateClientRequestStatusRequest(kind=kind, request_id=request_id, status=status)
    )
    await callback.answer(f"Статус: {REQUEST_STATUS_LABELS[status]}")
