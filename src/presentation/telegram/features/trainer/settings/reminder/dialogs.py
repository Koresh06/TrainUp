from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import SwitchTo, Cancel, Group, Select, Back
from aiogram_dialog.widgets.text import Const, Format

from .states import TrainerReminderSettingsSG
from .getters import (
    reminder_settings_getter,
    reminder_hours_getter,
)
from .handlers import (
    on_reminder_hours_selected,
)

trainer_reminder_settings_dialog = Dialog(
    Window(
        Format(
            "⏰ <b>Напоминания</b>\n\nЗа сколько часов до тренировки напоминать клиенту: {hours_before} ч."
        ),
        SwitchTo(
            Const("Изменить"),
            id="edit_hours",
            state=TrainerReminderSettingsSG.edit_hours,
        ),
        Cancel(Const("⬅️ Назад")),
        state=TrainerReminderSettingsSG.main,
        getter=reminder_settings_getter,
    ),
    Window(
        Const("Выбери, за сколько часов напоминать клиенту:"),
        Group(
            Select(
                Format("{item[label]}"),
                id="reminder_hours_select",
                item_id_getter=lambda item: item["id"],
                items="hours",
                on_click=on_reminder_hours_selected,
            ),
            width=4,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerReminderSettingsSG.edit_hours,
        getter=reminder_hours_getter,
    ),
)
