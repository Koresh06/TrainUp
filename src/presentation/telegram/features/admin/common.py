from decimal import Decimal

from aiogram_dialog import DialogManager

from src.application.use_cases.payment._shared import usd
from src.application.use_cases.stats.period import StatsPeriod

ADMIN_PERIOD_KEY = "period_admin"


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
