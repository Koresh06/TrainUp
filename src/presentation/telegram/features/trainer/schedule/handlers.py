from datetime import datetime, timezone

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Select, Button

from src.application.mediator import Mediator
from src.application.use_cases.slot_template.sync_weekday import SyncWeekdaySlotTemplatesRequest

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
    mediator: FromDishka[Mediator],
) -> None:
    weekday = int(item_id)
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    dialog_manager.dialog_data["selected_weekday"] = weekday

    templates: list[SlotTemplate] = await mediator.handle(
        GetActiveSlotTemplatesRequest(trainer_id=trainer_id)
    )
    active_times = {t.start_time for t in templates if t.weekday == weekday}

    await dialog_manager.switch_to(TrainerScheduleSG.manage_weekday)

    multiselect = dialog_manager.find("weekday_times_multiselect")
    await multiselect.reset_checked()
    for t in active_times:
        await multiselect.set_checked(t.strftime("%H:%M"), True)


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
        )
    )

    await callback.answer("Сохранено, календарь обновлён")
    await dialog_manager.switch_to(TrainerScheduleSG.main)
