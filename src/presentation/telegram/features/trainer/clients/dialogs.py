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
    debtors_getter,
    inactive_getter,
    package_detail_getter,
    package_paid_getter,
    package_sessions_getter,
    package_valid_getter,
    packages_getter,
    unpaid_getter,
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
    on_all_paid,
    on_debtor_selected,
    on_invite_back,
    on_open_progress,
    on_package_close,
    on_package_create_paid,
    on_package_create_unpaid,
    on_package_mark_paid,
    on_package_price_input,
    on_package_price_skip,
    on_package_selected,
    on_package_sessions_input,
    on_package_sessions_selected,
    on_package_valid_selected,
    on_unpaid_booking_selected,
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
from .validaters import (
    validate_any_phone,
    validate_client_name,
    validate_note,
    validate_price,
    validate_sessions,
)

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
            Format("😴 Давно не были ({inactive_count})"),
            id="inactive",
            state=TrainerClientsSG.inactive,
            when="has_inactive",
        ),
        SwitchTo(
            Format("💵 Должники ({debtors_count})"),
            id="debtors",
            state=TrainerClientsSG.debtors,
            when="has_debtors",
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
        Button(
            Const("📣 Позвать на тренировку"),
            id="invite_back",
            on_click=on_invite_back,
            when="can_invite_back",
        ),
        Button(Const("📈 Прогресс"), id="progress", on_click=on_open_progress),
        Row(
            SwitchTo(Const("🎫 Абонементы"), id="packages", state=TrainerClientsSG.packages),
            SwitchTo(
                Const("💵 Оплаты"), id="unpaid", state=TrainerClientsSG.unpaid, when="has_unpaid"
            ),
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
    # --- абонементы ---
    Window(
        Format("🎫 <b>Абонементы · {full_name}</b>{empty_hint}"),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="packages_select",
                item_id_getter=lambda item: item["id"],
                items="packages",
                on_click=on_package_selected,
            ),
            id="packages_scroll",
            width=1,
            height=6,
            hide_on_single_page=True,
        ),
        SwitchTo(
            Const("➕ Новый абонемент"), id="new_package", state=TrainerClientsSG.package_sessions
        ),
        to_card,
        state=TrainerClientsSG.packages,
        getter=packages_getter,
    ),
    Window(
        Format("{card}"),
        Button(
            Const("💵 Отметить оплату"),
            id="package_paid",
            on_click=on_package_mark_paid,
            when="can_pay",
        ),
        Button(
            Const("🗄 Закрыть абонемент"),
            id="package_close",
            on_click=on_package_close,
            when="can_close",
        ),
        SwitchTo(Const("⬅️ К абонементам"), id="to_packages", state=TrainerClientsSG.packages),
        state=TrainerClientsSG.package_detail,
        getter=package_detail_getter,
    ),
    Window(
        Const("🎫 Сколько занятий в абонементе?\n<i>Или введите своё число</i>"),
        Group(
            Select(
                Format("{item[label]}"),
                id="package_sessions_select",
                item_id_getter=lambda item: item["id"],
                items="options",
                on_click=on_package_sessions_selected,
            ),
            width=5,
        ),
        TextInput(
            id="package_sessions_input",
            type_factory=validate_sessions,
            on_success=on_package_sessions_input,
            on_error=on_input_error,
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_packages", state=TrainerClientsSG.packages),
        state=TrainerClientsSG.package_sessions,
        getter=package_sessions_getter,
    ),
    Window(
        Const("💰 Стоимость абонемента (BYN)?"),
        TextInput(
            id="package_price_input",
            type_factory=validate_price,
            on_success=on_package_price_input,
            on_error=on_input_error,
        ),
        Button(Const("Без цены ➡️"), id="package_no_price", on_click=on_package_price_skip),
        SwitchTo(Const("⬅️ Назад"), id="back_to_sessions", state=TrainerClientsSG.package_sessions),
        state=TrainerClientsSG.package_price,
    ),
    Window(
        Const("📅 Срок действия абонемента:"),
        Group(
            Select(
                Format("{item[label]}"),
                id="package_valid_select",
                item_id_getter=lambda item: item["id"],
                items="options",
                on_click=on_package_valid_selected,
            ),
            width=2,
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_price", state=TrainerClientsSG.package_price),
        state=TrainerClientsSG.package_valid,
        getter=package_valid_getter,
    ),
    Window(
        Format("{summary}\n\nАбонемент уже оплачен?"),
        Button(
            Const("✅ Да, оплачен"),
            id="package_create_paid",
            on_click=on_package_create_paid,
            style=Style(style=ButtonStyle.SUCCESS),
        ),
        Button(
            Const("⏳ Оплатит позже"),
            id="package_create_unpaid",
            on_click=on_package_create_unpaid,
            when="has_price",
        ),
        SwitchTo(Const("⬅️ Назад"), id="back_to_valid", state=TrainerClientsSG.package_valid),
        state=TrainerClientsSG.package_paid,
        getter=package_paid_getter,
    ),
    # --- оплаты ---
    Window(
        Format(
            "💵 <b>Неоплаченные тренировки</b>\nИтого: {total}\n\n"
            "Нажмите на тренировку, чтобы отметить её оплаченной."
        ),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="unpaid_select",
                item_id_getter=lambda item: item["id"],
                items="bookings",
                on_click=on_unpaid_booking_selected,
            ),
            id="unpaid_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        Button(
            Const("✅ Оплачено всё"), id="all_paid", on_click=on_all_paid, when="has_unpaid"
        ),
        to_card,
        state=TrainerClientsSG.unpaid,
        getter=unpaid_getter,
    ),
    Window(
        Format("💵 <b>Должники</b>\nВсего не оплачено: {total}"),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="debtors_select",
                item_id_getter=lambda item: item["id"],
                items="clients",
                on_click=on_debtor_selected,
            ),
            id="debtors_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        SwitchTo(Const("⬅️ К списку"), id="debtors_back", state=TrainerClientsSG.list),
        state=TrainerClientsSG.debtors,
        getter=debtors_getter,
    ),
    Window(
        Format(
            "😴 <b>Давно не были</b>\n\n"
            "Ходили, но уже больше {days} дней без тренировок и никуда не записаны. "
            "Откройте карточку — там кнопка «📣 Позвать на тренировку»."
        ),
        ScrollingGroup(
            Select(
                Format("{item[label]}"),
                id="inactive_select",
                item_id_getter=lambda item: item["id"],
                items="clients",
                on_click=on_debtor_selected,
            ),
            id="inactive_scroll",
            width=1,
            height=8,
            hide_on_single_page=True,
        ),
        SwitchTo(Const("⬅️ К списку"), id="inactive_back", state=TrainerClientsSG.list),
        state=TrainerClientsSG.inactive,
        getter=inactive_getter,
    ),
    on_start=on_clients_start,
)
