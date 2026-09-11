from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel, Group, Select, Back, Button
from aiogram_dialog.widgets.text import Const, Format

from src.presentation.telegram.features.slot_style import slot_style
from src.presentation.telegram.widgets.booking_calendar import BookingCalendar

from .states import TrainerRecurringSG
from .handlers import (
    on_client_selected,
    on_recurring_confirm,
    on_recurring_date_clicked,
    on_recurring_time_clicked,
)
from .getters import (
    recurring_confirm_getter,
    recurring_times_getter,
    select_client_getter,
    recurring_day_calendar_getter,
)

trainer_recurring_dialog = Dialog(
    Window(
        Const("Выберите клиента для постоянной записи:"),
        Group(
            Select(
                Format("{item[label]}"),
                id="recurring_client_select",
                item_id_getter=lambda item: item["id"],
                items="clients",
                on_click=on_client_selected,
            ),
            width=1,
        ),
        Cancel(Const("⬅️ Назад")),
        state=TrainerRecurringSG.select_client,
        getter=select_client_getter,
    ),
    Window(
        Const("Выберите день для постоянной тренировки:"),
        BookingCalendar(
            id="recurring_calendar",
            on_click=on_recurring_date_clicked,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerRecurringSG.select_day,
        getter=recurring_day_calendar_getter,
    ),
    Window(
        Format("Открытые слоты на {selected_day_label}:"),
        Group(
            Select(
                Format("{item[label]}"),
                id="recurring_time_select",
                items="times",
                item_id_getter=lambda item: item["value_id"],
                on_click=on_recurring_time_clicked,
                style=slot_style,
            ),
            width=2,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerRecurringSG.select_time,
        getter=recurring_times_getter,
    ),
    Window(
        Format(
            "Проверьте данные:\n\n"
            "👤 Клиент: {client_name}\n"
            "📅 {date} ({weekday_label}) в {time}\n\n"
            "Тренировка будет автоматически повторяться каждую неделю "
            "в <b>{weekday_label}</b> в это же время."
        ),
        Button(
            Const("✅ Добавить"),
            id="confirm_recurring",
            on_click=on_recurring_confirm,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerRecurringSG.confirm,
        getter=recurring_confirm_getter,
    ),
)
