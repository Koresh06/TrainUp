from aiogram import F
from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Cancel,
    Group,
    Row,
    ScrollingGroup,
    Select,
    SwitchTo,
)
from aiogram_dialog.widgets.link_preview import LinkPreview
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Const, Format

from src.domain.enums.client import ClientEditableField
from src.presentation.telegram.features.error_handler import on_input_error
from src.presentation.telegram.widgets.booking_calendar import BookingCalendar

from .getters import (
    book_confirm_getter,
    book_day_getter,
    book_time_getter,
    client_detail_getter,
    clients_list_getter,
    edit_menu_getter,
    edit_value_getter,
    invite_getter,
)
from .handlers import (
    on_add_name_success,
    on_add_note_skip,
    on_add_note_success,
    on_add_phone_skip,
    on_add_phone_success,
    on_book_confirm,
    on_book_day_clicked,
    on_book_time_clicked,
    on_client_item_selected,
    on_clients_start,
    on_delete_confirm,
    on_edit_field_click,
    on_edit_value_clear,
    on_edit_value_input,
)
from .states import TrainerClientsSG
from .validaters import validate_any_phone, validate_client_name, validate_note

to_card = SwitchTo(Const("⬅️ К карточке"), id="to_card", state=TrainerClientsSG.detail)

clients_trainer_dialog = Dialog(
    Window(
        Format("👥 <b>Мои клиенты</b>\n\n{summary}\n\n🔁 — постоянный · 📵 — без Telegram"),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="clients_list_select",
                item_id_getter=lambda item: item["id"],
                items="clients",
                on_click=on_client_item_selected,
            ),
            id="clients_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        SwitchTo(
            Const("➕ Добавить клиента без Telegram"),
            id="add_client",
            state=TrainerClientsSG.add_name,
        ),
        Cancel(Const("⬅️ Назад")),
        state=TrainerClientsSG.list,
        getter=clients_list_getter,
    ),
    Window(
        Format("{card}"),
        SwitchTo(
            Const("📅 Записать на тренировку"),
            id="book",
            state=TrainerClientsSG.book_day,
        ),
        Row(
            SwitchTo(Const("✏️ Изменить"), id="edit", state=TrainerClientsSG.edit_menu),
            SwitchTo(
                Const("🔗 Пригласить в бота"),
                id="invite",
                state=TrainerClientsSG.invite,
                when="is_offline",
            ),
        ),
        SwitchTo(
            Const("🗑 Удалить карточку"),
            id="delete",
            state=TrainerClientsSG.delete_confirm,
            when="is_offline",
        ),
        SwitchTo(
            Const("⬅️ К списку"), id="to_list", state=TrainerClientsSG.list, when=~F["from_outside"]
        ),
        Cancel(Const("⬅️ Назад"), when="from_outside"),
        LinkPreview(is_disabled=True),
        state=TrainerClientsSG.detail,
        getter=client_detail_getter,
    ),
    # --- новый клиент ---
    Window(
        Const(
            "➕ <b>Новый клиент без Telegram</b>\n\n"
            "Карточка нужна для учёта: вы записываете клиента на тренировки, "
            "видите его в расписании и статистике. Бот ему ничего не пишет.\n\n"
            "Введите <b>имя и фамилию</b> (фамилию можно не указывать):"
        ),
        TextInput(
            id="add_name_input",
            type_factory=validate_client_name,
            on_success=on_add_name_success,
            on_error=on_input_error,
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_list", state=TrainerClientsSG.list),
        state=TrainerClientsSG.add_name,
    ),
    Window(
        Const("📞 Телефон клиента:"),
        TextInput(
            id="add_phone_input",
            type_factory=validate_any_phone,
            on_success=on_add_phone_success,
            on_error=on_input_error,
        ),
        Button(Const("Пропустить ➡️"), id="skip_phone", on_click=on_add_phone_skip),
        SwitchTo(Const("⬅️ Назад"), id="back_to_name", state=TrainerClientsSG.add_name),
        state=TrainerClientsSG.add_phone,
    ),
    Window(
        Const(
            "📝 Заметка о клиенте — видите только вы\n"
            "(цели, ограничения по здоровью, как платит):"
        ),
        TextInput(
            id="add_note_input",
            type_factory=validate_note,
            on_success=on_add_note_success,
            on_error=on_input_error,
        ),
        Button(Const("Пропустить ➡️"), id="skip_note", on_click=on_add_note_skip),
        SwitchTo(Const("⬅️ Назад"), id="back_to_phone", state=TrainerClientsSG.add_phone),
        state=TrainerClientsSG.add_note,
    ),
    # --- редактирование ---
    Window(
        Format("✏️ <b>{full_name}</b>\n\nЧто изменить?"),
        Group(
            Button(
                Const("Имя"),
                id=ClientEditableField.FIRST_NAME.value,
                on_click=on_edit_field_click,
                when="is_offline",
            ),
            Button(
                Const("Фамилия"),
                id=ClientEditableField.LAST_NAME.value,
                on_click=on_edit_field_click,
                when="is_offline",
            ),
            Button(
                Const("Телефон"),
                id=ClientEditableField.PHONE.value,
                on_click=on_edit_field_click,
                when="is_offline",
            ),
            Button(
                Const("📝 Заметка"),
                id=ClientEditableField.TRAINER_NOTE.value,
                on_click=on_edit_field_click,
            ),
            width=2,
        ),
        to_card,
        state=TrainerClientsSG.edit_menu,
        getter=edit_menu_getter,
    ),
    Window(
        Format("{prompt}"),
        TextInput(id="edit_value_input", on_success=on_edit_value_input),
        Button(
            Const("🧹 Очистить"),
            id="clear_value",
            on_click=on_edit_value_clear,
            when="can_clear",
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_edit", state=TrainerClientsSG.edit_menu),
        state=TrainerClientsSG.edit_value,
        getter=edit_value_getter,
    ),
    Window(
        Format(
            "🔗 <b>Персональная ссылка для {full_name}</b>\n\n"
            "<code>{link}</code>\n\n"
            "Перешлите её клиенту. Когда он откроет ссылку в Telegram, карточка "
            "станет его аккаунтом: вся история и записи сохранятся, а бот начнёт "
            "присылать ему напоминания. Ссылка одноразовая."
        ),
        to_card,
        LinkPreview(is_disabled=True),
        state=TrainerClientsSG.invite,
        getter=invite_getter,
    ),
    Window(
        Const(
            "🗑 Удалить карточку клиента?\n\n"
            "Удалить можно только карточку без тренировок — например, созданную по ошибке."
        ),
        Button(
            Const("🗑 Да, удалить"),
            id="delete_confirm",
            on_click=on_delete_confirm,
            style=Style(style=ButtonStyle.DANGER),
        ),
        to_card,
        state=TrainerClientsSG.delete_confirm,
    ),
    # --- запись клиента ---
    Window(
        Format("📅 Запись для <b>{full_name}</b>\n\nВыберите день:"),
        BookingCalendar(id="book_calendar", on_click=on_book_day_clicked),
        to_card,
        state=TrainerClientsSG.book_day,
        getter=book_day_getter,
    ),
    Window(
        Format("🕐 Свободное время на {day_label}:"),
        Group(
            Select(
                Format("{item[label]}"),
                id="book_time_select",
                items="times",
                item_id_getter=lambda item: item["value_id"],
                on_click=on_book_time_clicked,
            ),
            width=3,
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_day", state=TrainerClientsSG.book_day),
        state=TrainerClientsSG.book_time,
        getter=book_time_getter,
    ),
    Window(
        Format(
            "Записать <b>{full_name}</b>\n\n📅 {day_label} в {time}\n\n"
            "Запись сразу будет подтверждена.\n{notify_hint}"
        ),
        Button(
            Const("✅ Записать"),
            id="book_confirm",
            on_click=on_book_confirm,
            style=Style(style=ButtonStyle.SUCCESS),
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_time", state=TrainerClientsSG.book_time),
        state=TrainerClientsSG.book_confirm,
        getter=book_confirm_getter,
    ),
    on_start=on_clients_start,
)
