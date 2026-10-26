"""«🏖 Отпуск / больничный» в кабинете тренера."""

from src.application.use_cases.vacation.manage import GetVacationsRequest
from tests.presentation.conftest import TRAINER_TG
from tests.presentation.test_ui_flows import activate_subscription


async def test_trainer_closes_period(ui, run, trainer_setup) -> None:
    trainer, tomorrow = trainer_setup["trainer"], trainer_setup["tomorrow"]
    await activate_subscription(run, trainer.id)

    await ui.send(TRAINER_TG, "/trainer")
    await ui.click(TRAINER_TG, "⚙️ Настройки")
    await ui.click(TRAINER_TG, "🚫 Блокировки")
    assert "Запланированных периодов нет" in await ui.click(TRAINER_TG, "🏖 Отпуск / больничный")
    await ui.click(TRAINER_TG, "➕ Закрыть период")
    await ui.click(TRAINER_TG, str(tomorrow.day))
    preview = await ui.click(TRAINER_TG, str(tomorrow.day))
    assert "Закроется слотов: 1" in preview
    assert "Слотов закрыто: 1" in await ui.click(TRAINER_TG, "✅ Закрыть период")

    await ui.click(TRAINER_TG, "⬅️ Назад")
    [vacation] = await run(GetVacationsRequest(trainer_id=trainer.id))
    assert vacation.date_from == vacation.date_to == tomorrow
    await ui.click(TRAINER_TG, next(b for b in ui.buttons if b.startswith("🏖")))
    await ui.click(TRAINER_TG, "🗑 Удалить период")
    assert await run(GetVacationsRequest(trainer_id=trainer.id)) == []
