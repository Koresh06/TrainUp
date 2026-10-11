from datetime import datetime

from aiogram.types import Chat, InlineKeyboardButton, InlineKeyboardMarkup, Message, User
from aiogram_dialog.test_tools.keyboard import InlineButtonTextLocator

from src.application.use_cases.access.get_user_access import GetUserAccessRequest
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.infrastructure.database.seed import seed_subscription_price_plans
from src.infrastructure.notifications.callback_data.payment import (
    ManualPaymentAction,
    ManualPaymentCD,
)

TRAINER_TG = 5001
ADMIN_TG = 777000


async def _trainer_without_subscription(run, container):
    await seed_subscription_price_plans(container)
    return await run(
        RegisterTrainerRequest(tg_id=TRAINER_TG, name="Тренер", bio="", notification_chat_id=-100)
    )


async def _open_payment_methods(ui) -> None:
    assert "Выбери тариф" in await ui.send(TRAINER_TG, "/trainer")
    plan_button = next(b for b in ui.buttons if b.startswith("1 месяц"))
    assert "$30" in plan_button  # цены подписок — в долларах
    assert "Выберите способ оплаты" in await ui.click(TRAINER_TG, plan_button)


async def test_test_payment_opens_cabinet(ui, run, container) -> None:
    await _trainer_without_subscription(run, container)
    await _open_payment_methods(ui)
    assert ui.buttons[:2] == ["🤝 Через администратора", "🧪 Тестовая оплата"]

    assert "Тестовая оплата проведена" in await ui.click(TRAINER_TG, "🧪 Тестовая оплата")
    assert "Кабинет тренера" in await ui.click(TRAINER_TG, "🏋 В кабинет")


async def test_manual_payment_approved_by_admin(ui, run, container, notifications) -> None:
    await _trainer_without_subscription(run, container)
    await _open_payment_methods(ui)
    text = await ui.click(TRAINER_TG, "🤝 Через администратора")
    assert "@trainup_admin" in text and "💳 Оплатить" not in ui.buttons

    [request] = notifications.of("notify_manual_payment_request")
    # сообщение заявки у админа (как его отправил бы TelegramNotificationService)
    admin_message = Message(
        message_id=999,
        date=datetime.now(),
        chat=Chat(id=ADMIN_TG, type="private"),
        from_user=User(id=1, is_bot=True, first_name="bot"),
        text="Заявка на ручную оплату",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="✅ Оплата получена",
                    callback_data=ManualPaymentCD(
                        action=ManualPaymentAction.APPROVE, external_id=request.external_id
                    ).pack(),
                )
            ]]
        ),
    )

    # чужой пользователь кнопкой не воспользуется
    await ui.client(TRAINER_TG).click(admin_message, InlineButtonTextLocator("✅ Оплата получена"))
    assert not (await run(GetUserAccessRequest(tg_id=TRAINER_TG))).trainer_subscription_active

    await ui.client(ADMIN_TG).click(admin_message, InlineButtonTextLocator("✅ Оплата получена"))
    assert (await run(GetUserAccessRequest(tg_id=TRAINER_TG))).trainer_subscription_active
    assert [e.event.value for e in notifications.of("notify_subscription")] == ["paid"]
