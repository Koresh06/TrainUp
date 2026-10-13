"""UI: онбординг с пробным периодом, экран подписки, статистика/графики тренера
и аналитика пользователей в админке."""

import time
from datetime import datetime
from pathlib import Path

from aiogram.enums import ChatMemberStatus
from aiogram.types import (
    ChatMemberBanned,
    ChatMemberMember,
    ChatShared,
    Message,
    PhotoSize,
    Update,
    User,
)

from src.application.use_cases.bot_user.track_activity import TrackUserActivityRequest
from src.domain.enums.subscription import SubscriptionSource
from src.infrastructure.database.seed import seed_subscription_price_plans
from src.infrastructure.repositories.bot_user.sqlalchemy import SQLAlchemyBotUserRepo
from src.presentation.telegram.charts.media import CHARTS_DIR
from tests.presentation.conftest import ADMIN_TG, CLIENT_TG, TRAINER_TG
from tests.presentation.test_ui_flows import activate_subscription, register_client

NEW_TRAINER_TG = 5050


async def _send_message(ui, user_id: int, **content) -> str:
    client = ui.client(user_id)
    ui.mm.reset_history()
    await client.dp.feed_update(
        client.bot,
        Update(
            update_id=client._new_update_id(),
            message=Message(
                message_id=client._new_message_id(), date=datetime.now(),
                chat=client.chat, from_user=client.user, **content,
            ),
        ),
    )
    return ui.text


def _assert_chart(ui) -> None:
    assert ui.last.photo, "окно графика без картинки"


def _new_charts(since: float) -> list[Path]:
    files = [f for f in CHARTS_DIR.glob("*.png") if f.stat().st_mtime >= since]
    assert all(f.read_bytes().startswith(b"\x89PNG") for f in files)
    return files


async def test_onboarding_gives_trial_and_sells_subscription(ui, run, container, monkeypatch) -> None:
    monkeypatch.setattr("src.core.dependencies.providers.use_cases.TRAINER_TRIAL_DAYS", 7)
    await seed_subscription_price_plans(container)

    assert "Добро пожаловать" in await ui.send(NEW_TRAINER_TG, "/trainer")
    assert "Что даёт подписка" in await ui.click(NEW_TRAINER_TG, "💎 Что умеет TrainUp")
    assert "Публичное имя" in await ui.click(NEW_TRAINER_TG, "🚀 Начать регистрацию")
    await ui.send(NEW_TRAINER_TG, "Иван Петров")
    await ui.send(NEW_TRAINER_TG, "+375291234567")
    await ui.send(NEW_TRAINER_TG, "Тренер по ОФП, 5 лет опыта")
    await _send_message(
        ui, NEW_TRAINER_TG, photo=[PhotoSize(file_id="ph", file_unique_id="u", width=1, height=1)]
    )
    assert "Уведомления" in await ui.click(NEW_TRAINER_TG, "➡️ Далее")
    assert "Проверь данные" in await _send_message(
        ui, NEW_TRAINER_TG, chat_shared=ChatShared(request_id=1, chat_id=-100500, title="Работа")
    )

    text = await ui.click(NEW_TRAINER_TG, "✅ Завершить")
    assert "пробный период активирован" in text
    assert "7 дней бесплатно" in text and "За 2 дня и 3 ч." in text

    assert "Пробный период до" in await ui.click(NEW_TRAINER_TG, "🏋 Открыть кабинет")
    text = await ui.click(NEW_TRAINER_TG, "💎 Подписка")
    assert "Сейчас пробный период" in text and "Что входит" in text
    assert any("$80 · $26.67/мес · −11%" in b for b in ui.buttons)
    assert "Что даёт подписка" in await ui.click(NEW_TRAINER_TG, "💎 Подробнее о возможностях")
    assert "Выбери тариф" in await ui.click(NEW_TRAINER_TG, "💳 Выбрать тариф")


async def test_trainer_stats_and_charts(ui, run, trainer_setup) -> None:
    await activate_subscription(run, trainer_setup["trainer"].id)
    await register_client(ui, trainer_setup["token"])

    await ui.send(TRAINER_TG, "/trainer")
    text = await ui.click(TRAINER_TG, "📊 Статистика")
    assert "Всего: <b>1</b> (+1 новых)" in text and "Средний чек" in text

    started = time.time() - 1
    assert "Тренировки" in await ui.click(TRAINER_TG, "📈 Графики")
    _assert_chart(ui)
    assert "Доход" in await ui.click(TRAINER_TG, "💰 Доход")
    assert "Загрузка" in await ui.click(TRAINER_TG, "🗓 Загрузка")
    await ui.click(TRAINER_TG, "Всё")
    assert "🟢 🗓 Загрузка" in ui.buttons and "🟢 Всё" in ui.buttons
    _assert_chart(ui)
    await ui.click(TRAINER_TG, "🏋 Тренировки")
    _assert_chart(ui)
    # разные графики — разные файлы (имя = хэш содержимого, file_id не перепутается)
    assert len(_new_charts(started)) >= 3
    assert "Статистика · Всё время" in await ui.click(TRAINER_TG, "⬅️ К цифрам")


async def test_admin_user_analytics_and_charts(ui, run, session, trainer_setup) -> None:
    await activate_subscription(run, trainer_setup["trainer"].id)
    await register_client(ui, trainer_setup["token"])  # клиент отмечается middleware
    await run(TrackUserActivityRequest(tg_id=9999))  # нажал /start и ушёл

    # клиент заблокировал бота, потом передумал — и снова заблокировал
    client = ui.client(CLIENT_TG)
    bot_user = User(id=42, is_bot=True, first_name="bot")
    member = ChatMemberMember(user=bot_user, status=ChatMemberStatus.MEMBER)
    kicked = ChatMemberBanned(user=bot_user, status=ChatMemberStatus.KICKED, until_date=0)
    await client.my_chat_member_update(member, kicked)
    await client.my_chat_member_update(kicked, member)
    await client.my_chat_member_update(member, kicked)
    assert (await SQLAlchemyBotUserRepo(session).get_by_tg_id(CLIENT_TG)).is_bot_blocked

    await ui.send(ADMIN_TG, "/admin")
    await ui.click(ADMIN_TG, "📊 Статистика")
    text = await ui.click(ADMIN_TG, "👥 Пользователи")
    # админ, клиент и «гость»; тренер из фикстуры зарегистрирован в обход бота
    assert "Всего писали боту: <b>3</b>" in text
    assert "Без регистрации: 2" in text
    assert "Сейчас: <b>1</b>" in text
    assert "Конверсия пробный → оплата" in text

    await ui.click(ADMIN_TG, "📈 Графики")
    for button, caption in (
        ("🔥 Активность", "Активность"),
        ("💰 Выручка", "Выручка"),
        ("🏋 Занятия", "Занятия"),
        ("👥 Новые", "Новые пользователи"),
    ):
        assert caption in await ui.click(ADMIN_TG, button)
        _assert_chart(ui)
    await ui.click(ADMIN_TG, "Неделя")
    _assert_chart(ui)
    assert "Оплаты подписок" in await ui.click(ADMIN_TG, "⬅️ К цифрам")


async def test_trial_line_only_for_trial(ui, run, trainer_setup) -> None:
    from src.application.use_cases.subscription.grant import GrantSubscriptionRequest

    await run(
        GrantSubscriptionRequest(
            trainer_id=trainer_setup["trainer"].id, source=SubscriptionSource.TRIAL, days=7
        )
    )
    assert "Пробный период до" in await ui.send(TRAINER_TG, "/trainer")
