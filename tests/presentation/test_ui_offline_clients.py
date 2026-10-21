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
