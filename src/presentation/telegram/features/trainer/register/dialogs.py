from aiogram import F
from aiogram.enums import ButtonStyle, ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.kbd import (
    Select,
    Column,
    Button,
    Back,
    Next,
    RequestContact,
    SwitchTo,
    Url,
)
from aiogram_dialog.widgets.markup.reply_keyboard import ReplyKeyboardFactory

from src.presentation.telegram.features.error_handler import on_input_error
from src.presentation.telegram.features.handlers_phone import (
    on_phone_input_success,
    on_phone_received_contact,
    validate_phone_number,
)

from src.presentation.telegram.widgets.request_chat import RequestChat

from .handlers import (
    on_back_to_cabinet,
    on_delete_photo,
    on_group_chat_shared,
    on_group_message_forwarded,
    on_onboarding_confirm,
    on_photo_received,
    on_plan_selected,
    on_payment_method_selected,
    on_trial_open_cabinet,
)
from .getters import (
    getter_media,
    onboarding_final_getter,
    select_plan_getter,
    select_method_getter,
    payment_getter,
    trial_started_getter,
    welcome_getter,
)
from .texts import BENEFITS_FULL
from .validaters import validate_trainer_name, validate_trainer_bio
from .states import SubscriptionSG, TrainerOnboardingSG

trainer_onboarding_dialog = Dialog(
    Window(
        Format(
            "👋 <b>Добро пожаловать в TrainUp!</b>\n\n"
            "Бот берёт на себя запись клиентов, расписание и напоминания — "
            "тебе останется только проводить тренировки.\n\n"
            "<b>Что дальше:</b>\n"
            "1️⃣ Заполним профиль — имя, описание и группу для уведомлений\n"
            "{welcome_step_two}\n\n"
            "После этого откроется твой кабинет, и клиенты смогут "
            "записываться по персональной ссылке.\n\n"
            "⏱ Это займёт пару минут."
        ),
        SwitchTo(Const("💎 Что умеет TrainUp"), id="welcome_benefits", state=TrainerOnboardingSG.benefits),
        Next(Const("🚀 Начать")),
        state=TrainerOnboardingSG.welcome,
        getter=welcome_getter,
    ),
    Window(
        Const(
            "👤 <b>Публичное имя</b>\n\n"
            "Как тебя будут видеть клиенты? Например:\n"
            "<i>«Иван Петров, фитнес-тренер»</i>"
        ),
        TextInput(
            id="name",
            type_factory=validate_trainer_name,
            on_success=Next(),
            on_error=on_input_error,
        ),
        state=TrainerOnboardingSG.name,
    ),
    Window(
        Const(
            "📞 <b>Укажите Ваш номер телефона (например, "
            "+375291234567 или 80291234567):</b>"
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
        Back(Const("⬅️ Назад")),
        markup_factory=ReplyKeyboardFactory(
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
        state=TrainerOnboardingSG.phone,
    ),
    Window(
        Const(
            "📝 <b>О себе</b>\n\n"
            "Коротко: специализация, опыт, подход к тренировкам. "
            "Клиенты увидят это при первом входе."
        ),
        TextInput(
            id="bio",
            type_factory=validate_trainer_bio,
            on_success=Next(),
            on_error=on_input_error,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerOnboardingSG.bio,
    ),
    Window(
        Const(
            "🖼 <b>Фото</b>\n\n" "Отправь фото, которое увидят клиенты в твоём профиле.",
            when=~F["media"],
        ),
        Const("📸 <b>Ваше фото</b>", when="media"),
        DynamicMedia(selector="media", when="media"),
        MessageInput(
            func=on_photo_received,
            content_types=[ContentType.PHOTO],
        ),
        Button(
            Const("❌ Удалить фото"),
            id="delete_photo",
            on_click=on_delete_photo,
            when="file_id",
            style=Style(style=ButtonStyle.DANGER),
        ),
        Next(Const("➡️ Далее"), when="media"),
        Back(Const("⬅️ Назад")),
        state=TrainerOnboardingSG.photo,
        getter=getter_media,
    ),
    Window(
        Const(
            "🔔 <b>Уведомления</b>\n\n"
            "Последний шаг — куда слать уведомления о новых записях и заявках.\n\n"
            "Нажми кнопку ниже и выбери рабочую группу или канал — Telegram сам "
            "добавит туда бота администратором.\n\n"
            "Можно и по-старому: добавь бота админом в канал и перешли сюда "
            "любое сообщение из канала."
        ),
        RequestChat(Const("👥 Выбрать группу"), request_id=1, chat_is_channel=False),
        RequestChat(Const("📢 Выбрать канал"), request_id=2, chat_is_channel=True),
        MessageInput(
            func=on_group_chat_shared,
            content_types=[ContentType.CHAT_SHARED],
        ),
        MessageInput(
            func=on_group_message_forwarded,
            content_types=[ContentType.ANY],
        ),
        Back(Const("⬅️ Назад")),
        markup_factory=ReplyKeyboardFactory(
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
        state=TrainerOnboardingSG.group,
    ),
    Window(
        Format(
            "✅ <b>Проверь данные</b>\n\n"
            "👤 Имя: {name}\n"
            "📝 О себе: {bio}\n"
            "📞 Телефон: {phone}\n"
            "🔔 Уведомления: {chat_label}\n\n"
            "Всё верно?"
        ),
        DynamicMedia(selector="photo"),
        Button(
            Const("✅ Завершить"),
            id="finish_onboarding",
            on_click=on_onboarding_confirm,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerOnboardingSG.final,
        getter=onboarding_final_getter,
    ),
    Window(
        Format(
            "🎉 <b>Профиль создан — пробный период активирован!</b>\n\n"
            "🎁 {trial_days} бесплатно, до <b>{trial_until}</b>. Все возможности "
            "открыты, оплата не нужна.\n\n"
            "<b>Чтобы клиенты начали записываться:</b>\n"
            "1️⃣ «⚙️ Настройки» → расписание: отметь дни и время тренировок\n"
            "2️⃣ «🔗 Тренерская ссылка»: отправь её клиентам или закрепи в соцсетях\n"
            "3️⃣ Новые записи придут в рабочую группу — подтверждай одной кнопкой\n\n"
            "{warning_line}"
        ),
        Button(Const("🏋 Открыть кабинет"), id="trial_to_cabinet", on_click=on_trial_open_cabinet),
        state=TrainerOnboardingSG.trial_started,
        getter=trial_started_getter,
    ),
    # окна вне основного пути — в конце: Next/Back ходят по порядку окон
    Window(
        Const(BENEFITS_FULL),
        SwitchTo(Const("🚀 Начать регистрацию"), id="benefits_start", state=TrainerOnboardingSG.name),
        SwitchTo(Const("⬅️ Назад"), id="benefits_back", state=TrainerOnboardingSG.welcome),
        state=TrainerOnboardingSG.benefits,
    ),
)


subscription_dialog = Dialog(
    Window(
        Format(
            "💳 <b>Подписка TrainUp</b>\n\n"
            "{status_line}\n\n"
            "<b>Что входит:</b>\n{benefits}\n\n"
            "{per_day_line}"
            "Если подписка ещё действует — новый срок добавится к текущему.\n\n"
            "Выбери тариф:"
        ),
        Column(
            Select(
                Format("{item[label]}"),
                id="plan_select",
                items="plans",
                item_id_getter=lambda item: item["id"],
                on_click=on_plan_selected,
            ),
        ),
        SwitchTo(Const("💎 Подробнее о возможностях"), id="to_benefits", state=SubscriptionSG.benefits),
        Button(Const("⬅️ В кабинет"), id="to_cabinet", on_click=on_back_to_cabinet),
        state=SubscriptionSG.select_plan,
        getter=select_plan_getter,
    ),
    Window(
        Format(
            "🧾 <b>Оплата подписки</b>\n\n"
            "Тариф: {plan_label}\n"
            "Стоимость: <b>{price}</b>\n\n"
            "Выберите способ оплаты:"
        ),
        Const("⚠️ Онлайн-оплата пока не подключена — обратитесь к администратору.", when="no_methods"),
        Column(
            Select(
                Format("{item[label]}"),
                id="payment_method_select",
                items="methods",
                item_id_getter=lambda item: item["id"],
                on_click=on_payment_method_selected,
            ),
        ),
        Back(Const("⬅️ Назад")),
        state=SubscriptionSG.select_method,
        getter=select_method_getter,
    ),
    Window(
        Format("{instructions}"),
        Url(Const("💳 Оплатить"), Format("{payment_url}"), when="has_url"),
        Button(Const("🏋 В кабинет"), id="paid_to_cabinet", on_click=on_back_to_cabinet, when="is_paid"),
        SwitchTo(
            Const("🔁 Другой способ оплаты"),
            id="to_methods",
            state=SubscriptionSG.select_method,
        ),
        state=SubscriptionSG.payment,
        getter=payment_getter,
    ),
    # вне основного пути — в конце: Back/next() ходят по порядку окон
    Window(
        Const(BENEFITS_FULL),
        SwitchTo(Const("💳 Выбрать тариф"), id="benefits_to_plans", state=SubscriptionSG.select_plan),
        state=SubscriptionSG.benefits,
    ),
)
