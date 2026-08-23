from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Select,
    Column,
    Group,
    Cancel,
    Back,
    Button,
    Multiselect,
)
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput

from src.presentation.telegram.features.error_handler import on_input_error

from .handlers import (
    on_capacity_entered,
    on_keep_capacity,
    on_weekday_selected,
    on_weekday_times_confirm,
)
from .getters import (
    capacity_getter,
    weekday_list_getter,
    weekday_times_getter,
)
from .validaters import validate_capacity
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
            "Вместимость слота для {weekday_label}: <b>{current_capacity}</b>\n\n"
            "Оставить как есть, или для изменения введите новое число:"
        ),
        Button(
            Const("✅ Оставить"),
            id="keep_capacity",
            on_click=on_keep_capacity,
        ),
        TextInput(
            id="capacity_input",
            type_factory=validate_capacity,
            on_success=on_capacity_entered,
            on_error=on_input_error,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerScheduleSG.manage_weekday_capacity,
        getter=capacity_getter,
    ),
    Window(
        Format("Настрой время для: {weekday_label}"),
        Group(
            Multiselect(
                Format("✅ {item[label]}"),
                Format("⬜ {item[label]}"),
                id="weekday_times_multiselect",
                item_id_getter=lambda item: item["id"],
                items="times",
            ),
            width=4,
        ),
        Button(
            Const("💾 Подтвердить"),
            id="confirm_weekday_times",
            on_click=on_weekday_times_confirm,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerScheduleSG.manage_weekday,
        getter=weekday_times_getter,
    ),
)
