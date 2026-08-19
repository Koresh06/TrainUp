from aiogram.enums import ButtonStyle, ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Multiselect,
    Button,
    Group,
    Next,
    RequestContact,
    Back,
    Select,
)
from aiogram_dialog.widgets.markup.reply_keyboard import ReplyKeyboardFactory
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.style import Style

from src.presentation.telegram.features.error_handler import on_input_error
from .states import ClientRegisterSG
from .validator import (
    bounded_text,
    validate_full_name,
    validate_phone_number,
    validate_age,
)
from .handlers import (
    on_full_name_success,
    on_goals_done,
    on_health_conditions_done,
    on_health_conditions_other_entered,
    on_health_entered,
    on_health_skip,
    on_injuries_entered,
    on_injuries_skip,
    on_phone_input_success,
    on_phone_received_contact,
    on_age_input_success,
    on_register_confirm,
    on_sport_experience_selected,
)
from .getters import (
    goals_getter,
    health_conditions_getter,
    sport_experience_getter,
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
        Const("👤 <b>Укажите Ваше имя и фамилию:</b>\nНапример: <i>Иван Иванов</i>"),
        TextInput(
            id="full_name",
            type_factory=validate_full_name,
            on_success=on_full_name_success,
            on_error=on_input_error,
        ),
        Back(Const("⬅️ Назад")),
        state=ClientRegisterSG.full_name,
    ),
    Window(
        Const("Укажите Ваш возраст"),
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
        Const("🏋️ <b>Ваш стаж занятий спортом или физической культурой:</b>"),
        Group(
            Select(
                Format("{item[label]}"),
                id="sport_experience_select",
                item_id_getter=lambda item: item["id"],
                items="sport_experience_options",
                on_click=on_sport_experience_selected,
            ),
            width=1,
        ),
        Back(Const("⬅️ Назад")),
        state=ClientRegisterSG.sport_experience,
        getter=sport_experience_getter,
    ),
    Window(
        Const(
            "❤️ <b>Ваше состояние здоровья и тела:</b>\n(можно выбрать несколько вариантов)"
        ),
        Group(
            Multiselect(
                Format("✅ {item[label]}"),
                Format("⬜ {item[label]}"),
                id="health_conditions_multiselect",
                item_id_getter=lambda item: item["id"],
                items="health_conditions_options",
            ),
            width=1,
        ),
        Button(
            Const("Далее ➡️"),
            id="health_conditions_done",
            on_click=on_health_conditions_done,
            style=Style(style=ButtonStyle.SUCCESS),
        ),
        Back(Const("⬅️ Назад")),
        state=ClientRegisterSG.health_conditions,
        getter=health_conditions_getter,
    ),
    Window(
        Const("Уточните, пожалуйста, детали:"),
        TextInput(
            id="health_conditions_other_input",
            type_factory=bounded_text(1000),
            on_success=on_health_conditions_other_entered,
            on_error=on_input_error,
        ),
        Back(Const("⬅️ Назад")),
        state=ClientRegisterSG.health_conditions_other,
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
            Const("Далее ➡️"),
            id="goals_done",
            on_click=on_goals_done,
            style=Style(style=ButtonStyle.SUCCESS),
        ),
        Back(Const("⬅️ Назад")),
        state=ClientRegisterSG.goals,
        getter=goals_getter,
    ),
    Window(
        Const("Есть ли особенности здоровья, о которых стоит знать тренеру?"),
        TextInput(
            id="health_input",
            type_factory=bounded_text(1000),
            on_success=on_health_entered,
            on_error=on_input_error,
        ),
        Button(
            Const("Пропустить"),
            id="skip_health",
            on_click=on_health_skip,
            style=Style(style=ButtonStyle.PRIMARY),
        ),
        Back(Const("⬅️ Назад")),
        state=ClientRegisterSG.health_notes,
    ),
    Window(
        Const("Есть ли травмы, которые нужно учитывать?"),
        TextInput(
            id="injuries_input",
            type_factory=bounded_text(1000),
            on_success=on_injuries_entered,
            on_error=on_input_error,
        ),
        Button(
            Const("Пропустить"),
            id="skip_injuries",
            on_click=on_injuries_skip,
            style=Style(style=ButtonStyle.PRIMARY),
        ),
        Back(Const("⬅️ Назад")),
        state=ClientRegisterSG.injuries,
    ),
    Window(
        Format(
            "Проверь данные:\n\n"
            "👤 {full_name}\n"
            "📞 {phone}\n"
            "🎂 {age} лет\n"
            "🏋️ Стаж: {sport_experience}\n"
            "❤️ Состояние здоровья: {health_conditions}\n"
            "🎯 Цели: {goals}\n"
            "📝 Особенности: {health_notes}\n"
            "🩹 Травмы: {injuries}"
        ),
        Button(
            Const("✅ Всё верно"),
            id="confirm_register",
            on_click=on_register_confirm,
            style=Style(style=ButtonStyle.SUCCESS),
        ),
        Back(Const("⬅️ Назад")),
        state=ClientRegisterSG.confirm,
        getter=register_confirm_getter,
    ),
)
