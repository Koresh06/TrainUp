from datetime import time, timedelta, timezone

import pytest

from src.application.use_cases.invite_link.get_active import GetActiveInviteLinkRequest
from src.application.use_cases.slot_template.sync_weekday import (
    SyncWeekdaySlotTemplatesRequest,
)
from src.application.use_cases.subscription.grant import GrantSubscriptionRequest
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.application.use_cases.faq.get_active import GetActiveFaqItemsRequest
from src.domain.enums.faq import FaqAudience
from src.domain.enums.subscription import SubscriptionSource
from src.domain.utils import get_project_today
from src.infrastructure.database.seed import seed_faq_items, seed_subscription_price_plans
from tests.presentation.conftest import BOT_CALLS

TRAINER_TG = 5001
CLIENT_TG = 6001
ADMIN_TG = 777000  # tests/conftest.py


@pytest.fixture
async def trainer_setup(run, container):
    await seed_subscription_price_plans(container)
    await seed_faq_items(container)
    trainer = await run(
        RegisterTrainerRequest(tg_id=TRAINER_TG, name="Тренер", bio="Био", notification_chat_id=-100)
    )
    tomorrow = get_project_today() + timedelta(days=1)
    await run(
        SyncWeekdaySlotTemplatesRequest(
            trainer_id=trainer.id, weekday=tomorrow.weekday(),
            time_capacities={time(10, 0, tzinfo=timezone.utc): 2},
        )
    )
    link = await run(GetActiveInviteLinkRequest(trainer_id=trainer.id))
    return {"trainer": trainer, "token": link.token, "tomorrow": tomorrow}


async def activate_subscription(run, trainer_id: int, days: int = 30) -> None:
    await run(GrantSubscriptionRequest(trainer_id=trainer_id, source=SubscriptionSource.TRIAL, days=days))


async def register_client(ui, token: str) -> None:
    assert "Привет" in await ui.send(CLIENT_TG, f"/start {token}")
    await ui.click(CLIENT_TG, "Начать →")
    for value in ["Пётр Петров", "30", "+375291234567"]:
        await ui.send(CLIENT_TG, value)
    await ui.click(CLIENT_TG, "Нет опыта")

    # «Другое» требует текст: без него «Далее» не пускает
    await ui.click(CLIENT_TG, "⬜ Другое")
    assert "напишите сообщением" in ui.text
    await ui.click(CLIENT_TG, "Далее ➡️")
    assert "Другое" in ui.text  # остались на вопросе
    await ui.send(CLIENT_TG, "болит колено")
    assert "✅ Другое: болит колено" in ui.buttons
    await ui.click(CLIENT_TG, "Далее ➡️")

    await ui.click(CLIENT_TG, "⬜ Базовая (Целевые мышцы)")
    assert "Проверь данные" in await ui.click(CLIENT_TG, "Далее ➡️")
    assert "Другое: болит колено" in ui.text
    assert "Выберите подходящую" in await ui.click(CLIENT_TG, "✅ Всё верно")


async def test_client_journey(ui, run, trainer_setup, notifications) -> None:
    await activate_subscription(run, trainer_setup["trainer"].id)
    await register_client(ui, trainer_setup["token"])

    await ui.click(CLIENT_TG, "📅 Записаться на занятия")
    await ui.click(CLIENT_TG, str(trainer_setup["tomorrow"].day))
    await ui.click(CLIENT_TG, "10:00 (2)")
    await ui.click(CLIENT_TG, "✅ Подтвердить")
    [new_booking] = notifications.of("notify_new_booking")
    assert ("Ваше состояние здоровья и тела", "Другое: болит колено") in new_booking.client_answers

    await ui.send(CLIENT_TG, "/start")
    assert "ожидает подтверждения" in await ui.click(CLIENT_TG, "📋 Мои записи")
    await ui.click(CLIENT_TG, "⬅️ Назад")

    await ui.click(CLIENT_TG, "🏋 Программа тренировок")
    await ui.click(CLIENT_TG, "Неделя (3 занятия)")
    await ui.click(CLIENT_TG, "Конкретная цель")
    assert "Пропустить ➡️" not in ui.buttons
    await ui.send(CLIENT_TG, "Подтянуться 10 раз <3")
    assert "&lt;3" in ui.text
    await ui.click(CLIENT_TG, "✅ Отправить заявку")

    await ui.click(CLIENT_TG, "✉️ Обратная связь")
    assert "+375291234567" in await ui.click(CLIENT_TG, "📞 Заказать обратный звонок")
    await ui.click(CLIENT_TG, "✅ Да, на этот номер")
    await ui.click(CLIENT_TG, "✉️ Обратная связь")
    await ui.click(CLIENT_TG, "❓ Частые вопросы")
    assert "наличными" in await ui.click(CLIENT_TG, "Как оплатить занятия?")
    await ui.click(CLIENT_TG, "⬅️ К вопросам")
    await ui.click(CLIENT_TG, "⬅️ Назад")
    await ui.click(CLIENT_TG, "⬅️ Назад")

    assert "Другое: болит колено" in await ui.click(CLIENT_TG, "📝 Моя анкета")
    await ui.click(CLIENT_TG, "✏️ Обновить ответы")
    assert "✅ Другое: болит колено" in ui.buttons  # ответ восстановлен с текстом
    await ui.click(CLIENT_TG, "Далее ➡️")
    await ui.click(CLIENT_TG, "Далее ➡️")
    assert "Моя анкета" in await ui.click(CLIENT_TG, "💾 Сохранить")

    assert len(notifications.of("notify_client_request")) == 2


async def test_trainer_cabinet(ui, run, trainer_setup) -> None:
    await activate_subscription(run, trainer_setup["trainer"].id)
    await register_client(ui, trainer_setup["token"])
    await ui.click(CLIENT_TG, "💬 Консультация с тренером")
    await ui.click(CLIENT_TG, "Бесплатная")
    await ui.click(CLIENT_TG, "Пропустить ➡️")
    await ui.click(CLIENT_TG, "✅ Отправить заявку")

    assert "Кабинет тренера" in await ui.send(TRAINER_TG, "/trainer")
    assert "Подписка до" in ui.text
    assert "📨 Заявки (1 🆕)" in ui.buttons

    await ui.click(TRAINER_TG, "📨 Заявки (1 🆕)")
    request_button = next(b for b in ui.buttons if b.startswith("💬"))
    assert "Новая" in await ui.click(TRAINER_TG, request_button)
    assert "В работе" in await ui.click(TRAINER_TG, "🛠 Взять в работу")
    await ui.click(TRAINER_TG, "⬅️ Назад")
    await ui.click(TRAINER_TG, "⬅️ Назад")

    await ui.click(TRAINER_TG, "⚙️ Настройки")
    await ui.click(TRAINER_TG, "🚫 Блокировка дней/слотов")
    await ui.click(TRAINER_TG, str(trainer_setup["tomorrow"].day))
    await ui.click(TRAINER_TG, "🟢 10:00 (0/2)")
    assert "🚫 10:00 (0/2)" in ui.buttons
    await ui.click(TRAINER_TG, "✅ Открыть весь день")
    assert "🟢 10:00 (0/2)" in ui.buttons
    for _ in range(3):
        await ui.click(TRAINER_TG, "⬅️ Назад")

    assert "Помощь" in await ui.click(TRAINER_TG, "❓ Помощь")
    assert "Как клиенты попадают ко мне?" in ui.buttons


async def test_expired_subscription_closes_cabinet_and_client_access(ui, run, trainer_setup) -> None:
    await activate_subscription(run, trainer_setup["trainer"].id)
    await register_client(ui, trainer_setup["token"])
    assert "Кабинет тренера" in await ui.send(TRAINER_TG, "/trainer")

    # подписка «закончилась»: помечаем её истёкшей прямо в БД
    from src.application.use_cases.subscription.get_active import GetActiveSubscriptionRequest
    from src.infrastructure.repositories.subscription.sqlalchemy import (
        SQLAlchemyTrainerSubscriptionRepo,
    )
    subscription = await run(GetActiveSubscriptionRequest(trainer_id=trainer_setup["trainer"].id))
    subscription.expired()
    from src.core.dependencies.providers import base
    async with base.async_session_maker() as session:
        await SQLAlchemyTrainerSubscriptionRepo(session).save(subscription)
        await session.commit()

    # кабинет: нажатие кнопки → сообщение и кнопка продления вместо действия
    await ui.click(TRAINER_TG, "📋 Бронирования")
    assert any("Подписка закончилась" in t for t in ui.sent_texts())

    # клиент: /start → тренер недоступен
    await ui.send(CLIENT_TG, "/start")
    assert any("сейчас недоступна" in t for t in ui.sent_texts())

    # /trainer ведёт на выбор тарифа
    assert "Выбери тариф" in await ui.send(TRAINER_TG, "/trainer")


async def test_admin_panel(ui, run, trainer_setup, task_queue) -> None:
    assert "Панель администратора" in await ui.send(ADMIN_TG, "/admin")

    assert "Статистика" in await ui.click(ADMIN_TG, "📊 Статистика")
    assert "Оплаты подписок" in ui.text
    assert "Всё время" in await ui.click(ADMIN_TG, "Всё")
    await ui.click(ADMIN_TG, "⬅️ Назад")

    await ui.click(ADMIN_TG, "👨‍🏫 Тренеры")
    trainer_button = next(b for b in ui.buttons if "Тренер" in b)
    assert trainer_button.startswith("⌛")  # подписки нет
    assert "нет активной подписки" in await ui.click(ADMIN_TG, trainer_button)
    await ui.click(ADMIN_TG, "🎁 Выдать подписку")
    await ui.click(ADMIN_TG, "🎁 Бесплатный / пробный период")
    assert "Бесплатный период: 14 дн." in await ui.click(ADMIN_TG, "14 дн.")
    await ui.click(ADMIN_TG, "✅ Выдать")
    assert "осталось" in ui.text
    await ui.click(ADMIN_TG, "⛔ Заблокировать")
    await ui.click(ADMIN_TG, "✅ Подтвердить")
    assert "заблокирован" in ui.text
    await ui.click(ADMIN_TG, "✅ Разблокировать")
    await ui.click(ADMIN_TG, "✅ Подтвердить")
    await ui.click(ADMIN_TG, "⬅️ К списку")
    await ui.click(ADMIN_TG, "⬅️ Назад")

    await ui.click(ADMIN_TG, "📢 Рассылка")
    await ui.click(ADMIN_TG, "👨‍🏫 Всем тренерам")
    assert "Так будет выглядеть" in await ui.send(ADMIN_TG, "Важное объявление")
    await ui.click(ADMIN_TG, "🚀 Отправить")
    assert [t for t, _ in task_queue.enqueued] == ["execute_mailing"]

    await ui.send(ADMIN_TG, "/admin")
    await ui.click(ADMIN_TG, "❓ FAQ")
    assert "FAQ тренеров" in await ui.click(ADMIN_TG, "👨‍🏫 FAQ тренеров")
    await ui.click(ADMIN_TG, "➕ Добавить вопрос")
    await ui.send(ADMIN_TG, "Как выйти из бота?")
    await ui.send(ADMIN_TG, "Никак 🙂")
    trainer_faq = await run(GetActiveFaqItemsRequest(audience=FaqAudience.TRAINER))
    assert trainer_faq[-1].question == "Как выйти из бота?"
    await ui.click(ADMIN_TG, "⬅️ Назад")
    await ui.click(ADMIN_TG, "⬅️ Назад")

    await ui.click(ADMIN_TG, "📥 Выгрузки (CSV)")
    await ui.click(ADMIN_TG, "👨‍🏫 Тренеры")
    assert any(type(m).__name__ == "SendDocument" for m in BOT_CALLS)


async def test_admin_blocks_client(ui, run, trainer_setup) -> None:
    await activate_subscription(run, trainer_setup["trainer"].id)
    await register_client(ui, trainer_setup["token"])

    await ui.send(ADMIN_TG, "/admin")
    await ui.click(ADMIN_TG, "👥 Клиенты")
    await ui.send(ADMIN_TG, "Пётр")
    client_button = next(b for b in ui.buttons if "Пётр" in b)
    await ui.click(ADMIN_TG, client_button)
    await ui.click(ADMIN_TG, "⛔ Заблокировать")
    assert "заблокирован" in ui.text

    await ui.send(CLIENT_TG, "/start")
    assert any("ограничен администратором" in t for t in ui.sent_texts())


async def test_admin_is_hidden_from_others(ui, trainer_setup) -> None:
    await ui.send(CLIENT_TG, "/admin")
    assert ui.last is None
