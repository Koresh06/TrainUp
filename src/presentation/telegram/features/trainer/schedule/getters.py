from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.slot_template.get_active import GetActiveSlotTemplatesRequest
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
    return {
        "weekday_label": WEEKDAY_LABELS_FULL[weekday],
        "times": [
            {"id": t.strftime("%H:%M"), "label": t.strftime("%H:%M")}
            for t in generate_time_options()
        ],
    }