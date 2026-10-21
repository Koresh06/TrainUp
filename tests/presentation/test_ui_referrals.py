"""Экраны реферальных программ: тренер приглашает тренера."""

import re

from src.application.use_cases.trainer.get_by_tg_id import GetTrainerByTgIdRequest
from tests.presentation.conftest import TRAINER_TG
from tests.presentation.test_ui_flows import activate_subscription


async def test_trainer_invites_trainer(ui, run, trainer_setup) -> None:
    await activate_subscription(run, trainer_setup["trainer"].id)
    await ui.send(TRAINER_TG, "/trainer")
    text = await ui.click(TRAINER_TG, "🎁 Пригласить тренера")
    assert "Как это работает" in text and "платную" in text
    code = re.search(r"start=(tr_[0-9a-f]+)", text).group(1)

    new_trainer = TRAINER_TG + 100
    welcome = await ui.send(new_trainer, f"/start {code}")
    assert "по приглашению коллеги" in welcome

    # уже зарегистрированный тренер по ссылке коллеги не регистрируется повторно
    await ui.send(TRAINER_TG, f"/start {code}")
    assert any("уже зарегистрированы как тренер" in t for t in ui.sent_texts())
    assert (await run(GetTrainerByTgIdRequest(tg_id=TRAINER_TG))).referred_by_trainer_id is None
