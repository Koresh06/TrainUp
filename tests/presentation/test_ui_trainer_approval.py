import pytest

from src.application.use_cases.staff.manage import (
    AddAdminRequest,
    ToggleAdminPermissionRequest,
)
from src.application.use_cases.trainer.get_by_tg_id import GetTrainerByTgIdRequest
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.core.dependencies.providers import use_cases as providers
from src.domain.enums.admin import AdminPermission
from tests.presentation.conftest import ADMIN_TG, BOT_CALLS, CLIENT_TG, TRAINER_TG


@pytest.fixture(autouse=True)
def approval_on(monkeypatch):
    monkeypatch.setattr(providers, "TRAINER_APPROVAL_REQUIRED", True)


async def _application(run) -> None:
    await run(
        RegisterTrainerRequest(
            tg_id=TRAINER_TG, name="Кандидат", bio="bio", notification_chat_id=-1
        )
    )


async def test_pending_trainer_has_no_cabinet(ui, run) -> None:
    await _application(run)
    BOT_CALLS.clear()
    await ui.send(TRAINER_TG, "/trainer")
    assert any("Заявка на проверке" in getattr(c, "text", "") for c in BOT_CALLS)


async def test_admin_approves_from_panel(ui, run) -> None:
    await _application(run)
    await ui.send(ADMIN_TG, "/admin")
    await ui.click(ADMIN_TG, "🛂 Заявки тренеров (1)")
    card = await ui.click(ADMIN_TG, "🕓 Кандидат")
    assert "Кандидат" in card and str(TRAINER_TG) in card

    await ui.click(ADMIN_TG, "✅ Подтвердить")
    assert (await run(GetTrainerByTgIdRequest(tg_id=TRAINER_TG))).is_approved


async def test_helper_needs_permission_for_applications(ui, run) -> None:
    await _application(run)
    await run(AddAdminRequest(added_by_tg_id=ADMIN_TG, tg_id=CLIENT_TG))
    await ui.send(CLIENT_TG, "/admin")
    assert not any("Заявки" in button for button in ui.buttons)

    await run(
        ToggleAdminPermissionRequest(
            tg_id=CLIENT_TG, permission=AdminPermission.TRAINERS_APPROVE
        )
    )
    await ui.send(CLIENT_TG, "/admin")
    assert "🛂 Заявки тренеров (1)" in ui.buttons
