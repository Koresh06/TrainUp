"""Дневник прогресса: тренер вносит замеры клиенту, клиент видит их у себя."""

from src.application.use_cases.client.get_by_tg_id import GetClientByTgIdRequest
from src.application.use_cases.progress.measurements import GetMeasurementsRequest
from tests.presentation.conftest import CLIENT_TG, TRAINER_TG
from tests.presentation.test_ui_flows import activate_subscription, register_client


async def test_progress_trainer_and_client(ui, run, trainer_setup) -> None:
    await activate_subscription(run, trainer_setup["trainer"].id)
    await register_client(ui, trainer_setup["token"])
    client = await run(GetClientByTgIdRequest(tg_id=CLIENT_TG))

    await ui.send(TRAINER_TG, "/trainer")
    await ui.click(TRAINER_TG, "👥 Мои клиенты")
    await ui.click(TRAINER_TG, "Пётр Петров")
    assert "Записей пока нет" in await ui.click(TRAINER_TG, "📈 Прогресс")
    await ui.click(TRAINER_TG, "➕ Новая запись")
    await ui.send(TRAINER_TG, "76 84")
    assert "Вес: <b>76 кг</b>" in await ui.click(TRAINER_TG, "✅ Сохранить без фото")
    assert "📊 График" not in ui.buttons  # одной точки мало

    # клиент сам записывает вес — у тренера видна динамика
    await ui.send(CLIENT_TG, "/start")
    await ui.click(CLIENT_TG, "📈 Мой прогресс")
    await ui.click(CLIENT_TG, "➕ Новая запись")
    await ui.send(CLIENT_TG, "73.5")
    text = await ui.click(CLIENT_TG, "✅ Сохранить без фото")
    assert "Мой прогресс" in text and "73.5 кг" in text and "−2.5" in text

    items = await run(GetMeasurementsRequest(client_id=client.id))
    assert [str(m.weight) for m in items] == ["76.0", "73.5"]

    await ui.click(CLIENT_TG, "📊 График")
    assert "Вес" in ui.text and "📏 Обхваты" in ui.buttons
    await ui.click(CLIENT_TG, "📏 Обхваты")
    assert "Обхваты" in ui.text
    await ui.click(CLIENT_TG, "⬅️ Назад")
    await ui.click(CLIENT_TG, "🗑 Удалить последнюю")
    await ui.click(CLIENT_TG, "🗑 Удалить")
    assert len(await run(GetMeasurementsRequest(client_id=client.id))) == 1
