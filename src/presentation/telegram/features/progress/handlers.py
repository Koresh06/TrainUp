from decimal import Decimal
from typing import Any

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput
from aiogram_dialog.widgets.kbd import Button, Select

from src.application.mediator import Mediator
from src.application.use_cases.progress.measurements import (
    AddMeasurementRequest,
    DeleteMeasurementRequest,
    GetMeasurementsRequest,
)
from src.domain.enums.booking import BookingActor

from .getters import GIRTH_CHART, WEIGHT_CHART
from .states import ProgressSG


async def on_values_input(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    value: dict[str, Decimal | None],
) -> None:
    dialog_manager.dialog_data["new_values"] = {k: str(v) if v is not None else None for k, v in value.items()}
    await dialog_manager.switch_to(ProgressSG.add_photo)


async def on_only_photo(callback: CallbackQuery, button: Button, dialog_manager: DialogManager) -> None:
    dialog_manager.dialog_data["new_values"] = {}
    await dialog_manager.switch_to(ProgressSG.add_photo)


async def _save(dialog_manager: DialogManager, mediator: Mediator, photo_file_id: str | None) -> bool:
    values = dialog_manager.dialog_data.pop("new_values", {})
    if not any(values.values()) and photo_file_id is None:
        return False
    await mediator.handle(
        AddMeasurementRequest(
            client_id=dialog_manager.start_data["client_id"],
            added_by=(
                BookingActor.TRAINER
                if dialog_manager.start_data.get("as_trainer")
                else BookingActor.CLIENT
            ),
            photo_file_id=photo_file_id,
            **{k: Decimal(v) for k, v in values.items() if v is not None},
        )
    )
    await dialog_manager.switch_to(ProgressSG.main)
    return True


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
    await _save(dialog_manager, mediator, message.photo[-1].file_id)


@inject
async def on_save_without_photo(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    if not await _save(dialog_manager, mediator, None):
        await callback.answer("Пришлите фото или вернитесь и введите замеры", show_alert=True)
        dialog_manager.dialog_data["new_values"] = {}
        return
    await callback.answer("✅ Сохранено")


async def on_chart_kind(callback: CallbackQuery, button: Button, dialog_manager: DialogManager) -> None:
    dialog_manager.dialog_data["chart"] = GIRTH_CHART if button.widget_id == "girth" else WEIGHT_CHART


async def on_photo_selected(
    callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str
) -> None:
    dialog_manager.dialog_data["photo_id"] = int(item_id)
    await dialog_manager.switch_to(ProgressSG.photo)


@inject
async def on_delete_last(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    client_id: int = dialog_manager.start_data["client_id"]
    items = await mediator.handle(GetMeasurementsRequest(client_id=client_id))
    if items:
        await mediator.handle(DeleteMeasurementRequest(client_id=client_id, measurement_id=items[-1].id))
    await callback.answer("Удалено")
    await dialog_manager.switch_to(ProgressSG.main)


async def on_progress_start(start_data: Any, dialog_manager: DialogManager) -> None:
    dialog_manager.dialog_data["chart"] = WEIGHT_CHART
