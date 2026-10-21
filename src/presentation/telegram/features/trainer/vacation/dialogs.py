from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, ScrollingGroup, Select, SwitchTo
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Const, Format

from src.presentation.telegram.widgets.booking_calendar import FutureScheduleCalendar

from .getters import (
    detail_getter,
    done_getter,
    pick_calendar_getter,
    preview_getter,
    vacations_getter,
)
from .handlers import (
    on_from_picked,
    on_to_picked,
    on_vacation_confirm,
    on_vacation_delete,
    on_vacation_selected,
)
from .states import TrainerVacationSG

to_list = SwitchTo(Const("⬅️ Назад"), id="to_list", state=TrainerVacationSG.list)

trainer_vacation_dialog = Dialog(
    Window(
        Format(
            "🏖 <b>Отпуск / больничный</b>\n\n"
            "Закройте период целиком: все слоты станут недоступны, записи "
            "отменятся, а клиенты получат сообщение с датами.{empty_hint}"
        ),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="vacations_select",
                item_id_getter=lambda item: item["id"],
                items="vacations",
                on_click=on_vacation_selected,
            ),
            id="vacations_scroll",
            width=1,
            height=6,
            hide_on_single_page=True,
        ),
        SwitchTo(Const("➕ Закрыть период"), id="new", state=TrainerVacationSG.pick_from),
        Cancel(Const("⬅️ Назад")),
        state=TrainerVacationSG.list,
        getter=vacations_getter,
    ),
    Window(
        Const("🏖 Первый день периода:\n<i>синим — дни с записями</i>"),
        FutureScheduleCalendar(id="vacation_from", on_click=on_from_picked),
        to_list,
        state=TrainerVacationSG.pick_from,
        getter=pick_calendar_getter,
    ),
    Window(
        Format("🏖 С {date_from}. Последний день периода:"),
        FutureScheduleCalendar(id="vacation_to", on_click=on_to_picked),
        SwitchTo(Const("⬅️ Назад"), id="back_from", state=TrainerVacationSG.pick_from),
        state=TrainerVacationSG.pick_to,
        getter=pick_calendar_getter,
    ),
    Window(
        Format("{text}"),
        Button(
            Const("✅ Закрыть период"),
            id="confirm",
            on_click=on_vacation_confirm,
            style=Style(style=ButtonStyle.DANGER),
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to", state=TrainerVacationSG.pick_to),
        state=TrainerVacationSG.preview,
        getter=preview_getter,
    ),
    Window(
        Format("{text}"),
        to_list,
        state=TrainerVacationSG.done,
        getter=done_getter,
    ),
    Window(
        Format(
            "🏖 <b>{period}</b>\n\n"
            "Вышли раньше? Удалите период — будущие слоты в нём снова откроются "
            "для записи. Отменённые записи не восстанавливаются."
        ),
        Button(
            Const("🗑 Удалить период"),
            id="delete",
            on_click=on_vacation_delete,
            style=Style(style=ButtonStyle.DANGER),
        ),
        to_list,
        state=TrainerVacationSG.detail,
        getter=detail_getter,
    ),
)
