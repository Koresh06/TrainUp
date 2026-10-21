"""Кабинет тренера: клиент без Telegram — карточка, запись, персональная ссылка."""

import re

from src.application.use_cases.client.get_by_tg_id import GetClientByTgIdRequest
from tests.presentation.conftest import CLIENT_TG, TRAINER_TG
from tests.presentation.test_ui_flows import activate_subscription


async def test_trainer_adds_and_books_offline_client(ui, run, trainer_setup) -> None:
    await activate_subscription(run, trainer_setup["trainer"].id)
    await ui.send(TRAINER_TG, "/trainer")
    await ui.click(TRAINER_TG, "👥 Мои клиенты")
    assert "Клиентов пока нет" in ui.text

    await ui.click(TRAINER_TG, "➕ Добавить клиента без Telegram")
    await ui.send(TRAINER_TG, "Олег Ким")
    assert "Не похоже на номер" not in await ui.send(TRAINER_TG, "+7 (999) 123-45-67")
    card = await ui.click(TRAINER_TG, "Пропустить ➡️")
    assert "Олег Ким" in card and "Без Telegram" in card and "+79991234567" in card

    await ui.click(TRAINER_TG, "📅 Записать на тренировку")
    await ui.click(TRAINER_TG, str(trainer_setup["tomorrow"].day))
    await ui.click(TRAINER_TG, "10:00 (2)")
    assert "предупредите его сами" in ui.text
    card = await ui.click(TRAINER_TG, "✅ Записать")
    assert "Ближайшие" in card and "10:00" in card

    await ui.click(TRAINER_TG, "✏️ Изменить")
    await ui.click(TRAINER_TG, "📝 Заметка")
    assert "колено" in await ui.send(TRAINER_TG, "колено, без прыжков")

    await ui.click(TRAINER_TG, "⬅️ К списку")
    assert "📵 Олег Ким" in ui.buttons
    await ui.click(TRAINER_TG, "📵 Олег Ким")

    link_text = await ui.click(TRAINER_TG, "🔗 Пригласить в бота")
    token = re.search(r"start=(cl_[0-9a-f]+)", link_text).group(1)

    # клиент открывает ссылку и подтверждает, что это он
    await ui.send(CLIENT_TG, f"/start {token}")
    assert any("добавил вас в свои клиенты" in t for t in ui.sent_texts())
    await ui.click_sent(CLIENT_TG, "✅ Да, это я")
    client = await run(GetClientByTgIdRequest(tg_id=CLIENT_TG))
    assert client.full_name == "Олег Ким"
    assert "Мои записи" in "".join(ui.buttons)


async def test_inactive_clients_screen(ui, run, trainer_setup, session, notifications) -> None:
    from datetime import time, timedelta

    from src.domain.enums.booking import BookingStatus
    from src.domain.utils import get_project_today
    from tests.factories import make_booking, make_client, make_slot

    trainer = trainer_setup["trainer"]
    await activate_subscription(run, trainer.id)
    lost = await make_client(session, trainer.id, tg_id=CLIENT_TG, first_name="Пропал")
    slot = await make_slot(session, trainer.id, get_project_today() - timedelta(days=40), time(10, 0))
    await make_booking(session, lost, slot, BookingStatus.COMPLETED)

    await ui.send(TRAINER_TG, "/trainer")
    await ui.click(TRAINER_TG, "👥 Мои клиенты")
    assert "Ходили, но уже больше" in await ui.click(TRAINER_TG, "😴 Давно не были (1)")
    await ui.click(TRAINER_TG, "Пропал — 40 дн.")
    await ui.click(TRAINER_TG, "📣 Позвать на тренировку")
    assert len(notifications.of("notify_plan_next_training")) == 1


async def test_referral_link_registration(ui, run, trainer_setup) -> None:
    import re

    from tests.presentation.test_ui_flows import register_client

    await activate_subscription(run, trainer_setup["trainer"].id)
    await register_client(ui, trainer_setup["token"])
    await ui.send(CLIENT_TG, "/start")
    text = await ui.click(CLIENT_TG, "🎁 Пригласить друга")
    code = re.search(r"start=(ref_[0-9a-f]+)", text).group(1)
    assert "📤 Поделиться" in ui.buttons

    friend_tg = CLIENT_TG + 1
    assert "Привет" in await ui.send(friend_tg, f"/start {code}")
    await ui.click(friend_tg, "Начать →")
    for value in ["Анна Друг", "25", "+375291234568"]:
        await ui.send(friend_tg, value)
    await ui.click(friend_tg, "Нет опыта")
    await ui.click(friend_tg, "⬜ Полностью здоров(-а)")
    await ui.click(friend_tg, "Далее ➡️")
    await ui.click(friend_tg, "⬜ Базовая (Целевые мышцы)")
    await ui.click(friend_tg, "Далее ➡️")
    await ui.click(friend_tg, "✅ Всё верно")

    friend = await run(GetClientByTgIdRequest(tg_id=friend_tg))
    me = await run(GetClientByTgIdRequest(tg_id=CLIENT_TG))
    assert friend.referred_by_client_id == me.id
