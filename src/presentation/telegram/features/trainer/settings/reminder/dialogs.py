from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, Group, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format

from .getters import (
    evening_digest_getter,
    morning_digest_getter,
    reminder_hours_getter,
    reminder_settings_getter,
)
from .handlers import (
    on_evening_hour_selected,
    on_evening_off,
    on_morning_hour_selected,
    on_morning_off,
    on_reminder_hours_selected,
    on_toggle_empty_days,
)
from .states import TrainerReminderSettingsSG


def _hours_select(widget_id: str, on_click) -> Group:
    return Group(
        Select(
            Format("{item[label]}"),
            id=widget_id,
            item_id_getter=lambda item: item["id"],
            items="hours",
            on_click=on_click,
        ),
        width=3,
    )


back = SwitchTo(Const("⬅️ Назад"), id="back_main", state=TrainerReminderSettingsSG.main)

trainer_reminder_settings_dialog = Dialog(
    Window(
        Format(
            "🔔 <b>Напоминания и сводки</b>\n\n"
            "⏰ Клиенту — за <b>{hours_before} ч.</b> до тренировки\n"
            "☀️ Вам сводка «сегодня у вас…» — <b>{morning}</b>\n"
            "🌙 Вам сводка «завтра у вас…» — <b>{evening}</b>\n\n"
            "<i>Сводка приходит в личные сообщения: список тренировок, "
            "заметки о клиентах и неподтверждённые записи.</i>"
        ),
        SwitchTo(
            Const("⏰ Напоминание клиенту"),
            id="edit_hours",
            state=TrainerReminderSettingsSG.edit_hours,
        ),
        SwitchTo(
            Const("☀️ Утренняя сводка"),
            id="morning",
            state=TrainerReminderSettingsSG.morning_digest,
        ),
        SwitchTo(
            Const("🌙 Вечерняя сводка"),
            id="evening",
            state=TrainerReminderSettingsSG.evening_digest,
        ),
        Button(
            Format("{empty_days} Присылать в дни без тренировок"),
            id="empty_days",
            on_click=on_toggle_empty_days,
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
        back,
        state=TrainerReminderSettingsSG.edit_hours,
        getter=reminder_hours_getter,
    ),
    Window(
        Const("☀️ Во сколько присылать сводку на сегодня?"),
        _hours_select("morning_select", on_morning_hour_selected),
        Button(Const("🔕 Выключить"), id="morning_off", on_click=on_morning_off, when="is_on"),
        back,
        state=TrainerReminderSettingsSG.morning_digest,
        getter=morning_digest_getter,
    ),
    Window(
        Const("🌙 Во сколько присылать сводку на завтра?"),
        _hours_select("evening_select", on_evening_hour_selected),
        Button(Const("🔕 Выключить"), id="evening_off", on_click=on_evening_off, when="is_on"),
        back,
        state=TrainerReminderSettingsSG.evening_digest,
        getter=evening_digest_getter,
    ),
)
