from src.application.use_cases.staff.get_access import GetAdminAccessRequest
from src.application.use_cases.staff.get_admins import GetAdminsRequest
from src.application.use_cases.staff.manage import (
    AddAdminRequest,
    ToggleAdminPermissionRequest,
)
from src.domain.enums.admin import AdminPermission
from tests.presentation.conftest import ADMIN_TG, CLIENT_TG


async def _helper(run, *permissions) -> None:
    await run(AddAdminRequest(added_by_tg_id=ADMIN_TG, tg_id=CLIENT_TG))
    for permission in permissions:
        await run(ToggleAdminPermissionRequest(tg_id=CLIENT_TG, permission=permission))


async def test_super_admin_adds_helper_and_grants_permission(ui, run, notifications) -> None:
    await ui.send(ADMIN_TG, "/admin")
    await ui.click(ADMIN_TG, "👮 Администраторы")
    await ui.click(ADMIN_TG, "➕ Добавить")
    card = await ui.send(ADMIN_TG, str(CLIENT_TG))
    assert str(CLIENT_TG) in card
    assert notifications.of("notify_admins")  # новому админу сказали про /admin

    await ui.click(ADMIN_TG, "⬜️ 📢 Рассылки")
    assert "✅ 📢 Рассылки" in ui.buttons
    access = await run(GetAdminAccessRequest(tg_id=CLIENT_TG))
    assert access.permissions == {AdminPermission.MAILING}


async def test_helper_sees_only_allowed_sections(ui, run) -> None:
    await _helper(run, AdminPermission.FAQ)
    text = await ui.send(CLIENT_TG, "/admin")
    assert "Оплат сегодня" not in text
    assert "❓ FAQ" in ui.buttons and "🔔 Уведомления" in ui.buttons
    assert "📊 Статистика" not in ui.buttons
    assert "👮 Администраторы" not in ui.buttons


async def test_stranger_has_no_admin_panel(ui) -> None:
    assert "Панель администратора" not in (await ui.send(CLIENT_TG, "/admin") or "")


async def test_revoked_permission_stops_working_in_open_window(ui, run) -> None:
    await _helper(run, AdminPermission.FAQ, AdminPermission.STATS)
    await ui.send(CLIENT_TG, "/admin")
    await run(ToggleAdminPermissionRequest(tg_id=CLIENT_TG, permission=AdminPermission.STATS))
    # кнопка осталась в уже открытом окне, но раздел не откроется
    text = await ui.click(CLIENT_TG, "📊 Статистика")
    assert "Статистика" not in text


async def test_muting_notification(ui) -> None:
    await ui.send(ADMIN_TG, "/admin")
    await ui.click(ADMIN_TG, "🔔 Уведомления")
    await ui.click(ADMIN_TG, "🔔 💸 Успешные оплаты")
    assert "🔕 💸 Успешные оплаты" in ui.buttons


async def test_remove_admin(ui, run) -> None:
    await _helper(run)
    await ui.send(ADMIN_TG, "/admin")
    await ui.click(ADMIN_TG, "👮 Администраторы")
    await ui.click(ADMIN_TG, ui.buttons[0])
    await ui.click(ADMIN_TG, "🗑 Удалить администратора")
    await ui.click(ADMIN_TG, "✅ Удалить")
    assert await run(GetAdminsRequest()) == []
    assert await run(GetAdminAccessRequest(tg_id=CLIENT_TG)) is None
