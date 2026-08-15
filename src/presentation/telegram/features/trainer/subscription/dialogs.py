from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.kbd import Select, Column, Button, Back, Next

from src.presentation.telegram.features.error_handler import on_input_error

from .handlers import (
    on_group_message_forwarded,
    on_onboarding_confirm,
    on_plan_selected,
    on_confirm_purchase,
)
from .getters import onboarding_final_getter, select_plan_getter, confirm_plan_getter
from .validaters import validate_trainer_name, validate_trainer_bio
from .states import SubscriptionSG, TrainerOnboardingSG

trainer_onboarding_dialog = Dialog(
    Window(
        Const(
            "👋 <b>Добро пожаловать в TrainUp!</b>\n\n"
            "Бот берёт на себя запись клиентов, расписание и напоминания — "
            "тебе останется только проводить тренировки.\n\n"
            "<b>Что дальше:</b>\n"
            "1️⃣ Заполним профиль — имя, описание и группу для уведомлений\n"
            "2️⃣ Выберешь тариф и оплатишь подписку\n\n"
            "После этого откроется твой кабинет, и клиенты смогут "
            "записываться по персональной ссылке.\n\n"
            "⏱ Это займёт пару минут."
        ),
        Next(Const("🚀 Начать")),
        state=TrainerOnboardingSG.welcome,
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
            "🔔 <b>Уведомления</b>\n\n"
            "Последний шаг — куда слать уведомления о новых записях:\n\n"
            "1. Создай группу или канал в Telegram\n"
            "2. Добавь туда бота как администратора\n"
            "3. Перешли сюда любое сообщение из этой группы/канала"
        ),
        MessageInput(
            func=on_group_message_forwarded,
            content_types=[ContentType.TEXT],
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerOnboardingSG.group,
    ),
    Window(
        Format(
            "✅ <b>Проверь данные</b>\n\n"
            "👤 Имя: {name}\n"
            "📝 О себе: {bio}\n"
            "🔔 Уведомления: {chat_label}\n\n"
            "Всё верно?"
        ),
        Button(
            Const("✅ Завершить"),
            id="finish_onboarding",
            on_click=on_onboarding_confirm,
        ),
        Back(Const("⬅️ Назад")),
        state=TrainerOnboardingSG.final,
        getter=onboarding_final_getter,
    ),
)


subscription_dialog = Dialog(
    Window(
        Const(
            "💳 <b>Подписка</b>\n\n"
            "У тебя нет активной подписки. Чтобы открыть кабинет тренера "
            "и доступ к боту для клиентов — выбери тариф:"
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
        state=SubscriptionSG.select_plan,
        getter=select_plan_getter,
    ),
    Window(
        Format(
            "🧾 <b>Подтверждение оплаты</b>\n\n"
            "Тариф: {plan_label}\n"
            "Стоимость: {price} BLR\n\n"
            "⚠️ <i>Это тестовая оплата — реальное списание не производится.</i>"
        ),
        Button(
            Const("💳 Оплатить"),
            id="confirm_purchase",
            on_click=on_confirm_purchase,
        ),
        Back(Const("⬅️ Назад")),
        state=SubscriptionSG.confirm,
        getter=confirm_plan_getter,
    ),
)
