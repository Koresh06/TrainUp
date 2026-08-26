from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.slot_template.get_active import (
    GetActiveSlotTemplatesRequest,
)
from src.domain.constants import WEEKDAY_LABELS_FULL, generate_time_options
from src.domain.entities.slot_template import SlotTemplate


@inject
async def weekday_list_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    templates: list[SlotTemplate] = await mediator.handle(
        GetActiveSlotTemplatesRequest(trainer_id=trainer_id)
    )
    count_by_weekday: dict[int, int] = {}
    for t in templates:
        count_by_weekday[t.weekday] = count_by_weekday.get(t.weekday, 0) + 1

    return {
        "weekdays": [
            {"id": str(i), "label": f"{label} ({count_by_weekday.get(i, 0)})"}
            for i, label in enumerate(WEEKDAY_LABELS_FULL)
        ]
    }


async def weekday_times_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    weekday: int = dialog_manager.dialog_data["selected_weekday"]
    capacities: dict[str, int] = dialog_manager.dialog_data.setdefault("capacities", {})

    times = []
    for t in generate_time_options():
        time_str = t.strftime("%H:%M")
        capacity = capacities.get(time_str, 0)
        label = f"✅ {time_str} ({capacity})" if capacity > 0 else time_str
        times.append({"id": time_str, "label": label})

    return {
        "weekday_label": WEEKDAY_LABELS_FULL[weekday],
        "times": times,
    }

async def edit_time_capacity_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    time_str: str = dialog_manager.dialog_data["editing_time"]
    capacities: dict[str, int] = dialog_manager.dialog_data.setdefault("capacities", {})
    capacity = capacities.get(time_str, 0)
    status_label = "Слот не активен" if capacity == 0 else f"Количество мест на слот: {capacity}"
    return {
        "time_str": time_str,
        "capacity": capacity,
        "status_label": status_label,
    }
