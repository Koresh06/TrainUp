"""Кабинет тренера: абонемент клиенту, оплата, должники."""

from decimal import Decimal

from src.application.use_cases.client.create_offline import CreateOfflineClientRequest
from src.application.use_cases.package.get_by_client import GetClientPackagesRequest
from tests.presentation.conftest import TRAINER_TG
from tests.presentation.test_ui_flows import activate_subscription


async def test_trainer_sells_package(ui, run, trainer_setup) -> None:
    trainer = trainer_setup["trainer"]
    await activate_subscription(run, trainer.id)
    client = await run(CreateOfflineClientRequest(trainer_id=trainer.id, first_name="Олег"))

    await ui.send(TRAINER_TG, "/trainer")
    await ui.click(TRAINER_TG, "👥 Мои клиенты")
    await ui.click(TRAINER_TG, "📵 Олег")
    assert "Абонементов пока нет" in await ui.click(TRAINER_TG, "🎫 Абонементы")
    await ui.click(TRAINER_TG, "➕ Новый абонемент")
    await ui.send(TRAINER_TG, "6")
    await ui.send(TRAINER_TG, "0")
    assert any("Сумма должна быть" in t for t in ui.sent_texts())
    await ui.send(TRAINER_TG, "120,5")
    await ui.click(TRAINER_TG, "30 дней")
    assert "6 занятий" in ui.text and "120.50 BYN" in ui.text
    await ui.click(TRAINER_TG, "⏳ Оплатит позже")

    [package] = await run(GetClientPackagesRequest(client_id=client.id))
    assert package.sessions_total == 6 and package.price == Decimal("120.50") and not package.is_paid

    await ui.click(TRAINER_TG, "⬅️ К карточке")
    assert "осталось <b>6</b> из 6" in ui.text and "не оплачен" in ui.text
    await ui.click(TRAINER_TG, "⬅️ К списку")
    assert "💵 Должники (1)" in ui.buttons
    await ui.click(TRAINER_TG, "💵 Должники (1)")
    await ui.click(TRAINER_TG, "Олег — 120.50 BYN")
    await ui.click(TRAINER_TG, "🎫 Абонементы")
    await ui.click(TRAINER_TG, "🎫 6 занятий · 0/6 💵")
    assert "✅ оплачен" in await ui.click(TRAINER_TG, "💵 Отметить оплату")
