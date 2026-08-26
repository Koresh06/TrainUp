from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Select,
    Column,
    Group,
    Cancel,
    Back,
    Button,
    Multiselect,
    Row,
)
from aiogram_dialog.widgets.text import Const, Format, Multi, Progress

from src.domain.constants import MAX_SLOT_CAPACITY
from src.presentation.telegram.features.trainer.settings.schedule.capacity_progress import CapacityProgress

from .handlers import (
    on_weekday_selected,
    on_time_selected,
    on_weekday_times_confirm,
    on_capacity_decrement,
    on_capacity_increment,
)
from .getters import (
    weekday_list_getter,
    edit_time_capacity_getter,
    weekday_times_getter,
)
from .states import TrainerScheduleSG

trainer_schedule_dialog = Dialog(
    Window(
        Const("Выбери день недели для настройки:"),
        Column(
            Select(
                Format("{item[label]}"),
                id="weekday_list_select",
                items="weekdays",
                item_id_getter=lambda item: item["id"],
                on_click=on_weekday_selected,
            ),
        ),
        Cancel(Const("⬅️ Назад")),
        state=TrainerScheduleSG.main,
        getter=weekday_list_getter,
    ),
    Window(
        Format(
            "Настрой время для: {weekday_label}\n\nВыбери время, чтобы задать вместимость:"
        ),
        Group(
            Select(
                Format("{item[label]}"),
                id="weekday_times_select",
                item_id_getter=lambda item: item["id"],
                items="times",
                on_click=on_time_selected,
            ),
            width=4,
        ),
        Button(
            Const("💾 Сохранить"),
            id="confirm_weekday_times",
            on_click=on_weekday_times_confirm,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerScheduleSG.manage_weekday,
        getter=weekday_times_getter,
    ),
    Window(
        Multi(
            Format("Время: <b>{time_str}</b>\n{status_label}"),
            CapacityProgress("capacity", MAX_SLOT_CAPACITY),
        ),
        Row(
            Button(
                Const("➖"),
                id="capacity_dec",
                on_click=on_capacity_decrement,
            ),
            Button(
                Const("➕"),
                id="capacity_inc",
                on_click=on_capacity_increment,
            ),
        ),
        Back(Const("✅ Готово")),
        state=TrainerScheduleSG.edit_time_capacity,
        getter=edit_time_capacity_getter,
    ),
)
