from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Cancel,
    Group,
    Select,
    Back,
    Button,
    ScrollingGroup,
    SwitchTo,
)
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.style import Style

from src.presentation.telegram.features.slot_style import slot_style
from src.presentation.telegram.widgets.booking_calendar import BookingCalendar

from .states import TrainerRecurringSG
from .handlers import (
    on_recurring_client_selected,
    on_client_selected,
    on_deactivate_recurring_click,
    on_edit_recurring_confirm,
    on_edit_recurring_date_clicked,
    on_edit_recurring_time_clicked,
    on_recurring_confirm,
    on_recurring_date_clicked,
    on_recurring_item_selected,
    on_recurring_time_clicked,
)
from .getters import (
    edit_recurring_confirm_getter,
    edit_recurring_times_getter,
    recurring_client_bookings_getter,
    recurring_confirm_getter,
    recurring_detail_getter,
    recurring_clients_getter,
    recurring_times_getter,
    select_client_getter,
    recurring_day_calendar_getter,
    edit_recurring_day_getter,
)

trainer_recurring_dialog = Dialog(
    Window(
        Const("🔁 <b>Постоянные клиенты</b>"),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="recurring_client_list_select",
                item_id_getter=lambda item: item["id"],
                items="recurring_list",
                on_click=on_recurring_client_selected,
            ),
            id="recurring_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        SwitchTo(
            Const("➕ Добавить"),
            id="add_recurring",
            state=TrainerRecurringSG.select_client,
            style=Style(style=ButtonStyle.SUCCESS),
        ),
        Cancel(Const("⬅️ Назад")),
        state=TrainerRecurringSG.list,
        getter=recurring_clients_getter,
    ),
    Window(
        Format("👤 <b>{client_name}</b>\n\nПостоянные тренировки:"),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="recurring_item_select",
                item_id_getter=lambda item: item["id"],
                items="recurring_list",
                on_click=on_recurring_item_selected,
            ),
            id="client_recurring_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerRecurringSG.client_bookings,
        getter=recurring_client_bookings_getter,
    ),
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
    Window(
        Format(
            "👤 Клиент: {client_name}\n" "📅 Каждую неделю: {weekday_label} в {time}"
        ),
        SwitchTo(
            Const("🔁 Изменить день/время"),
            id="edit_recurring_time",
            state=TrainerRecurringSG.edit_day,
        ),
        Button(
            Const("🛑 Остановить постоянную запись"),
            id="deactivate_recurring",
            on_click=on_deactivate_recurring_click,
            style=Style(style=ButtonStyle.DANGER),
        ),
        SwitchTo(
            Const("⬅️ Назад"),
            id="back_to_list",
            state=TrainerRecurringSG.client_bookings,
        ),
        state=TrainerRecurringSG.detail,
        getter=recurring_detail_getter,
    ),
    Window(
        Const("Выберите новый день/дату для постоянной тренировки:"),
        BookingCalendar(
            id="edit_recurring_calendar", on_click=on_edit_recurring_date_clicked
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerRecurringSG.edit_day,
        getter=edit_recurring_day_getter,
    ),
    Window(
        Format("Открытые слоты на {selected_day_label}:"),
        Group(
            Select(
                Format("{item[label]}"),
                id="edit_recurring_time_select",
                items="times",
                item_id_getter=lambda item: item["value_id"],
                on_click=on_edit_recurring_time_clicked,
            ),
            width=2,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerRecurringSG.edit_time,
        getter=edit_recurring_times_getter,
    ),
    Window(
        Format(
            "Новое расписание:\n\n"
            "📅 {weekday_label} в {time}\n\n"
            "Ближайшая тренировка будет перенесена на {date} {time}.\n"
            "Все последующие недели пойдут по новому графику."
        ),
        Button(
            Const("✅ Подтвердить"),
            id="confirm_edit_recurring",
            on_click=on_edit_recurring_confirm,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerRecurringSG.edit_confirm,
        getter=edit_recurring_confirm_getter,
    ),
)