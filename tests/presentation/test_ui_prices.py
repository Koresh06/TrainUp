"""Цены подписки в админке."""

from decimal import Decimal

from src.application.use_cases.staff.manage import (
    AddAdminRequest,
    ToggleAdminPermissionRequest,
)
from src.application.use_cases.subscription.get_active_price_plans import (
    GetActivePricePlansRequest,
)
from src.domain.enums.admin import AdminPermission
from src.domain.enums.subscription import SubscriptionPlan
from src.infrastructure.database.seed import seed_subscription_price_plans
from tests.presentation.conftest import ADMIN_TG, CLIENT_TG


async def _price(run, plan: SubscriptionPlan) -> Decimal:
    plans = await run(GetActivePricePlansRequest())
    return next(p.price for p in plans if p.plan == plan)



async def test_super_admin_changes_price(ui, run, container) -> None:
    await seed_subscription_price_plans(container)
    await ui.send(ADMIN_TG, "/admin")
    text = await ui.click(ADMIN_TG, "💲 Цены подписки")
    assert "3 месяца — $80" in text and "−11%" in text

    await ui.click(ADMIN_TG, "✏️ 1 месяц — $30")
    assert "Ошибка" not in await ui.send(ADMIN_TG, "0")
    assert "больше нуля" in ui.sent_texts()[-1]
    await ui.send(ADMIN_TG, "29.999")
    assert "двух знаков" in ui.sent_texts()[-1]

    text = await ui.send(ADMIN_TG, "29,99")
    assert any("Новая цена «1 месяц»" in t for t in ui.sent_texts())
    assert "1 месяц — $29.99" in text  # вернулись к списку с новой ценой
    assert await _price(run, SubscriptionPlan.ONE_MONTH) == Decimal("29.99")


async def test_prices_need_permission(ui, run, container) -> None:
    await seed_subscription_price_plans(container)
    await run(AddAdminRequest(added_by_tg_id=ADMIN_TG, tg_id=CLIENT_TG))
    await run(ToggleAdminPermissionRequest(tg_id=CLIENT_TG, permission=AdminPermission.FAQ))
    await ui.send(CLIENT_TG, "/admin")
    assert "💲 Цены подписки" not in ui.buttons

    await run(ToggleAdminPermissionRequest(tg_id=CLIENT_TG, permission=AdminPermission.PRICES))
    await ui.send(CLIENT_TG, "/admin")
    await ui.click(CLIENT_TG, "💲 Цены подписки")
    await run(ToggleAdminPermissionRequest(tg_id=CLIENT_TG, permission=AdminPermission.PRICES))
    # право отозвали, а окно открыто — цена не меняется
    await ui.click(CLIENT_TG, "✏️ 1 месяц — $30")
    await ui.send(CLIENT_TG, "1")
    assert await _price(run, SubscriptionPlan.ONE_MONTH) == Decimal("30")


async def test_super_admin_grants_prices_permission(ui) -> None:
    await ui.send(ADMIN_TG, "/admin")
    await ui.click(ADMIN_TG, "👮 Администраторы")
    await ui.click(ADMIN_TG, "➕ Добавить")
    await ui.send(ADMIN_TG, str(CLIENT_TG))
    await ui.click(ADMIN_TG, "⬜️ 💲 Цены подписки")
    assert "✅ 💲 Цены подписки" in ui.buttons
