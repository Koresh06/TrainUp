from datetime import datetime, timezone

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Select, Button
from aiogram_dialog.widgets.input import ManagedTextInput

from src.application.mediator import Mediator
from src.application.use_cases.slot_template.sync_weekday import (
    SyncWeekdaySlotTemplatesRequest,
)

from src.application.use_cases.slot_template.get_active import (
    GetActiveSlotTemplatesRequest,
)
from src.domain.entities.slot_template import SlotTemplate
from .states import TrainerScheduleSG


@inject
async def on_weekday_selected(
    callback: CallbackQuery,
    widget: Select[str],
    dialog_manager: DialogManager,
    item_id: str,
    /,
    mediator: FromDishka[Mediator],
) -> None:
    weekday = int(item_id)
    dialog_manager.dialog_data["selected_weekday"] = weekday

    trainer_id: int = dialog_manager.start_data["trainer_id"]
    templates: list[SlotTemplate] = await mediator.handle(
        GetActiveSlotTemplatesRequest(trainer_id=trainer_id)
    )
    weekday_templates = [t for t in templates if t.weekday == weekday]

    # текущая вместимость дня — берём у любого существующего шаблона этого дня
    # (они все должны быть одинаковыми, раз задаются одной цифрой на день)
    current_capacity = weekday_templates[0].capacity if weekday_templates else 1
    dialog_manager.dialog_data["current_capacity"] = current_capacity

    await dialog_manager.switch_to(TrainerScheduleSG.manage_weekday_capacity)


async def on_capacity_entered(
    message: Message,
    widget: ManagedTextInput[int],
    dialog_manager: DialogManager,
    value: int,
) -> None:
    dialog_manager.dialog_data["capacity"] = value
    await dialog_manager.switch_to(TrainerScheduleSG.manage_weekday)


async def on_keep_capacity(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data["capacity"] = dialog_manager.dialog_data.get(
        "current_capacity", 1
    )
    await dialog_manager.switch_to(TrainerScheduleSG.manage_weekday)


@inject
async def on_weekday_times_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    weekday: int = dialog_manager.dialog_data["selected_weekday"]
    capacity: int = dialog_manager.dialog_data["capacity"]

    multiselect = dialog_manager.find("weekday_times_multiselect")
    selected_ids: list[str] = multiselect.get_checked()
    selected_times = [
        datetime.strptime(s, "%H:%M").time().replace(tzinfo=timezone.utc)
        for s in selected_ids
    ]

    await mediator.handle(
        SyncWeekdaySlotTemplatesRequest(
            trainer_id=trainer_id,
            weekday=weekday,
            selected_times=selected_times,
            capacity=capacity,
        )
    )

    await callback.answer("Сохранено, календарь обновлён")
    await dialog_manager.switch_to(TrainerScheduleSG.main)
