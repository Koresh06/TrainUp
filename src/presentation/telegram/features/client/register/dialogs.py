from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Multiselect,
    Button,
    Group,
    Next,
    RequestContact,
    Back,
)
from aiogram_dialog.widgets.markup.reply_keyboard import ReplyKeyboardFactory
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput, MessageInput

from src.presentation.telegram.features.error_handler import on_input_error
from .states import ClientRegisterSG
from .validator import bounded_text, validate_phone_number, validate_age
from .handlers import (
    on_goals_done,
    on_health_entered,
    on_health_error,
    on_health_skip,
    on_injuries_entered,
    on_injuries_error,
    on_injuries_skip,
    on_phone_input_success,
    on_phone_received_contact,
    on_age_input_success,
    on_register_confirm,
)
from .getters import (
    goals_getter,
    welcome_getter,
    register_confirm_getter,
)

client_register_dialog = Dialog(
    Window(
        Format(
            "Привет! 👋\n\n"
            "Ты переходишь в бота тренера <b>{trainer_name}</b>.\n"
            "{trainer_bio}\n\n"
            "Для записи на тренировки нужно немного познакомиться — "
            "заполним короткую анкету."
        ),
        Next(Const("Начать →")),
        state=ClientRegisterSG.welcome,
        getter=welcome_getter,
    ),
    Window(
        Const(
            "📞 <b>Укажите Ваш номер телефона (с 8 или +7, без пробелов и лишних символов):</b>"
        ),
        RequestContact(Const("📞 Отправить номер")),
        MessageInput(
            func=on_phone_received_contact,
            content_types=[ContentType.CONTACT],
        ),
        TextInput(
            id="phone",
            type_factory=validate_phone_number,
            on_success=on_phone_input_success,
            on_error=on_input_error,
        ),
        markup_factory=ReplyKeyboardFactory(
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
        state=ClientRegisterSG.phone,
    ),
    Window(
        Const("Сколько тебе лет?"),
        TextInput(
            id="age",
            type_factory=validate_age,
            on_success=on_age_input_success,
            on_error=on_input_error,
        ),
        Back(Const("⬅️ Назад")),
        state=ClientRegisterSG.age,
    ),
    Window(
        Const("Выбери цели тренировок (можно несколько):"),
        Group(
            Multiselect(
                Format("✅ {item[label]}"),
                Format("⬜ {item[label]}"),
                id="goals_multiselect",
                item_id_getter=lambda item: item["id"],
                items="goals",
            ),
            width=1,
        ),
        Button(
            Const("Далее →"),
            id="goals_done",
            on_click=on_goals_done,
        ),
        state=ClientRegisterSG.goals,
        getter=goals_getter,
    ),
    Window(
        Const(
            "Есть ли особенности здоровья, о которых стоит знать тренеру? (до 250 символов)"
        ),
        TextInput(
            id="health_input",
            type_factory=bounded_text(250),
            on_success=on_health_entered,
            on_error=on_health_error,
        ),
        Button(Const("Пропустить"), id="skip_health", on_click=on_health_skip),
        state=ClientRegisterSG.health_notes,
    ),
    Window(
        Const("Есть ли травмы, которые нужно учитывать? (до 250 символов)"),
        TextInput(
            id="injuries_input",
            type_factory=bounded_text(250),
            on_success=on_injuries_entered,
            on_error=on_injuries_error,
        ),
        Button(Const("Пропустить"), id="skip_injuries", on_click=on_injuries_skip),
        state=ClientRegisterSG.injuries,
    ),
    Window(
        Format(
            "Проверь данные:\n\n"
            "📞 {phone}\n"
            "🎂 {age} лет\n"
            "🎯 Цели: {goals}\n"
            "❤️ Здоровье: {health_notes}\n"
            "🩹 Травмы: {injuries}"
        ),
        Button(
            Const("✅ Всё верно"),
            id="confirm_register",
            on_click=on_register_confirm,
        ),
        Back(Const("← Назад")),
        state=ClientRegisterSG.confirm,
        getter=register_confirm_getter,
    ),
)
