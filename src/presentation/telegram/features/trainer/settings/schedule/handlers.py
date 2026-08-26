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
from src.domain.constants import MAX_SLOT_CAPACITY
from src.domain.entities.slot_template import SlotTemplate
from .states import TrainerScheduleSG


@inject
async def on_weekday_selected(
    callback: CallbackQuery,
    widget: Select[str],
    dialog_manager: DialogManager,
    item_id: str,
    mediator: FromDishka[Mediator],
) -> None:
    weekday = int(item_id)
    dialog_manager.dialog_data["selected_weekday"] = weekday

    trainer_id: int = dialog_manager.start_data["trainer_id"]
    templates: list[SlotTemplate] = await mediator.handle(
        GetActiveSlotTemplatesRequest(trainer_id=trainer_id)
    )
    weekday_templates = [t for t in templates if t.weekday == weekday]

    dialog_manager.dialog_data["capacities"] = {
        t.start_time.strftime("%H:%M"): t.capacity for t in weekday_templates
    }

    await dialog_manager.next()


async def on_time_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["editing_time"] = item_id
    await dialog_manager.switch_to(TrainerScheduleSG.edit_time_capacity)


async def on_capacity_decrement(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    time_str: str = dialog_manager.dialog_data["editing_time"]
    capacities: dict[str, int] = dialog_manager.dialog_data.setdefault("capacities", {})
    capacities[time_str] = max(0, capacities.get(time_str, 0) - 1)


async def on_capacity_increment(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    time_str: str = dialog_manager.dialog_data["editing_time"]
    capacities: dict[str, int] = dialog_manager.dialog_data.setdefault("capacities", {})
    capacities[time_str] = min(MAX_SLOT_CAPACITY, capacities.get(time_str, 0) + 1)


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
    capacities: dict[str, int] = dialog_manager.dialog_data.get("capacities", {})

    time_capacities = {
        datetime.strptime(time_str, "%H:%M")
        .time()
        .replace(tzinfo=timezone.utc): capacity
        for time_str, capacity in capacities.items()
        if capacity > 0
    }

    await mediator.handle(
        SyncWeekdaySlotTemplatesRequest(
            trainer_id=trainer_id,
            weekday=weekday,
            time_capacities=time_capacities,
        )
    )

    await callback.answer("Сохранено, календарь обновлён")
    await dialog_manager.switch_to(TrainerScheduleSG.main)
