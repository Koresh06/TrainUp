from collections.abc import Awaitable, Callable
from decimal import Decimal
from functools import wraps

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager

from src.application.use_cases.payment._shared import usd
from src.application.use_cases.stats.period import StatsPeriod
from src.domain.entities.bot_admin import AdminAccess
from src.domain.enums.admin import AdminPermission
from src.presentation.telegram.middlewares.access import (
    ADMIN_ACCESS_KEY,
    NO_PERMISSION_TEXT,
)

ADMIN_PERIOD_KEY = "period_admin"


def current_admin(dialog_manager: DialogManager) -> AdminAccess | None:
    return dialog_manager.middleware_data.get(ADMIN_ACCESS_KEY)


def require_permission(*permissions: AdminPermission) -> Callable:
    """Для кнопок внутри раздела, где право уже́ раздела (тренера смотреть можно,
    а блокировать — нет): guard диалога это не различает, а скрытая кнопка не
    защищает от окна, открытого до отзыва права."""

    def decorator(handler: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
        @wraps(handler)
        async def wrapper(
            callback: CallbackQuery, widget, dialog_manager: DialogManager, *args, **kwargs
        ):
            admin = current_admin(dialog_manager)
            if admin is None or not admin.can(*permissions):
                await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
                return None
            return await handler(callback, widget, dialog_manager, *args, **kwargs)

        return wrapper

    return decorator


def money(amount: Decimal | int) -> str:
    # подписки и оплаты в админке — в долларах (как цены тарифов)
    return usd(Decimal(amount))


def progress_bar(part: int, total: int, width: int = 10) -> str:
    """▰▰▰▱▱ 60% — наглядная доля в текстовой статистике."""
    if total <= 0:
        return "▱" * width + " 0%"
    ratio = min(part / total, 1)
    filled = round(ratio * width)
    return "▰" * filled + "▱" * (width - filled) + f" {ratio:.0%}"


def percent(part: int, total: int) -> str:
    return f"{part / total:.0%}" if total else "0%"


def current_admin_period(dialog_manager: DialogManager) -> StatsPeriod:
    return StatsPeriod(
        dialog_manager.dialog_data.get(ADMIN_PERIOD_KEY, StatsPeriod.MONTH.value)
    )


async def on_admin_period_selected(callback, button, dialog_manager: DialogManager) -> None:
    dialog_manager.dialog_data[ADMIN_PERIOD_KEY] = button.widget_id
