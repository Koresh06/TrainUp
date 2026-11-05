"""Архив клиентов тренера: убрать, вернуть, клиент возвращается сам."""

from src.application.use_cases.booking.get_upcoming_by_client import (
    GetUpcomingBookingsByClientRequest,
)
from src.application.use_cases.client.get_by_tg_id import GetClientByTgIdRequest
from src.application.use_cases.client.get_clients_by_trainer import (
    GetClientsByTrainerIdRequest,
)
from src.application.use_cases.recurring_booking.get_all_active_by_trainer import (
    GetActiveRecurringBookingsByTrainerRequest,
)
from tests.presentation.conftest import CLIENT_TG, TRAINER_TG
from tests.presentation.test_ui_flows import activate_subscription, register_client



async def _client_with_booking(ui, run, trainer_setup) -> None:
    await activate_subscription(run, trainer_setup["trainer"].id)
    await register_client(ui, trainer_setup["token"])
    await ui.send(TRAINER_TG, "/trainer")
    await ui.click(TRAINER_TG, "👥 Мои клиенты")
    await ui.click(TRAINER_TG, "Пётр Петров")
    await ui.click(TRAINER_TG, "📅 Записать на тренировку")
    await ui.click(TRAINER_TG, f"{trainer_setup['tomorrow'].day:02d}")
    await ui.click(TRAINER_TG, "10:00 (2)")
    await ui.click(TRAINER_TG, "✅ Записать")


async def test_trainer_archives_and_client_comes_back(
    ui, run, trainer_setup, notifications
) -> None:
    trainer_id = trainer_setup["trainer"].id
    await _client_with_booking(ui, run, trainer_setup)
    client = await run(GetClientByTgIdRequest(tg_id=CLIENT_TG))
    assert await run(GetUpcomingBookingsByClientRequest(client_id=client.id))

    text = await ui.click(TRAINER_TG, "🗄 Убрать в архив")
    assert "будущие записи (1) отменятся" in text
    notifications.calls.clear()
    await ui.click(TRAINER_TG, "🗄 Да, убрать в архив")

    # клиент пропал из списка, запись отменена молча, клиенту одно сообщение
    assert "Пётр Петров" not in ui.buttons and "🗄 Архив (1)" in ui.buttons
    assert await run(GetUpcomingBookingsByClientRequest(client_id=client.id)) == []
    sent = notifications.of("send")
    assert len(sent) == 1 and "завершил с вами работу" in sent[0][1]
    assert await run(GetClientsByTrainerIdRequest(trainer_id=trainer_id)) == []

    # клиент не может записаться, но его карточка в базе осталась
    await ui.send(CLIENT_TG, "/start")
    assert "завершил с вами работу" in ui.sent_texts()[-1]

    # возвращается по ссылке тренера — снова в списке, тренеру сообщение
    notifications.calls.clear()
    await ui.send(CLIENT_TG, f"/start {trainer_setup['token']}")
    assert any("С возвращением" in t for t in ui.sent_texts())
    assert "Главное меню" in ui.text
    assert any("вернулся из архива" in text for _, text in notifications.of("send"))
    [back] = await run(GetClientsByTrainerIdRequest(trainer_id=trainer_id))
    assert back.id == client.id and not back.is_archived


async def test_trainer_restores_from_archive(ui, run, trainer_setup) -> None:
    trainer_id = trainer_setup["trainer"].id
    await _client_with_booking(ui, run, trainer_setup)
    await ui.click(TRAINER_TG, "🗄 Убрать в архив")
    await ui.click(TRAINER_TG, "🗄 Да, убрать в архив")

    await ui.click(TRAINER_TG, "🗄 Архив (1)")
    card = await ui.click(TRAINER_TG, next(b for b in ui.buttons if "Пётр Петров" in b))
    assert "В архиве с" in card
    assert "📅 Записать на тренировку" not in ui.buttons
    assert "⬅️ К архиву" in ui.buttons

    card = await ui.click(TRAINER_TG, "↩️ Вернуть из архива")
    assert "В архиве" not in card and "📅 Записать на тренировку" in ui.buttons
    assert len(await run(GetClientsByTrainerIdRequest(trainer_id=trainer_id))) == 1
    assert await run(GetActiveRecurringBookingsByTrainerRequest(trainer_id=trainer_id)) == []
