"""Профиль тренера: просмотр, редактирование, вид для клиента, группа."""

from src.application.use_cases.trainer.get_by_id import GetTrainerByIdRequest
from tests.presentation.conftest import TRAINER_TG
from tests.presentation.test_ui_flows import activate_subscription


async def test_trainer_edits_profile(ui, run, trainer_setup) -> None:
    trainer_id = trainer_setup["trainer"].id
    await activate_subscription(run, trainer_id)
    await ui.send(TRAINER_TG, "/trainer")
    text = await ui.click(TRAINER_TG, "👤 Профиль")
    assert "Тренер" in text and "Подписка: до" in text and "Клиентов: 0" in text

    await ui.click(TRAINER_TG, "✏️ Имя")
    assert "Иван <b>" not in await ui.send(TRAINER_TG, "Иван <Петров>")
    assert "Иван &lt;Петров&gt;" in ui.text

    await ui.click(TRAINER_TG, "📝 О себе")
    await ui.send(TRAINER_TG, "Силовые и ОФП, 10 лет опыта")
    await ui.click(TRAINER_TG, "🔗 Соцсети")
    await ui.send(TRAINER_TG, "Instagram: https://instagram.com/ivan")
    assert "Instagram" in ui.text

    preview = await ui.click(TRAINER_TG, "👁 Как меня видят клиенты")
    assert "Иван &lt;Петров&gt;" in preview and "10 лет опыта" in preview
    await ui.click(TRAINER_TG, "⬅️ Назад")

    await ui.click(TRAINER_TG, "📝 О себе")
    await ui.click(TRAINER_TG, "🧹 Очистить")
    await ui.click(TRAINER_TG, "🔔 Группа")
    assert "Группа для уведомлений" in ui.text

    trainer = await run(GetTrainerByIdRequest(trainer_id=trainer_id))
    assert trainer.name == "Иван <Петров>" and trainer.bio == ""
    assert trainer.social_links == {"Instagram": "https://instagram.com/ivan"}
