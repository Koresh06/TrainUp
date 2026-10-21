from datetime import date
from html import escape

from src.domain.entities.client_package import ClientPackage
from src.domain.enums.package import PackageStatus
from src.presentation.telegram.charts.text import byn

PACKAGE_STATUS_TITLES: dict[PackageStatus, str] = {
    PackageStatus.ACTIVE: "активен",
    PackageStatus.FINISHED: "все занятия использованы",
    PackageStatus.CANCELLED: "закрыт",
}


def package_line(package: ClientPackage, today: date, *, for_trainer: bool = True) -> str:
    """«🎫 8 занятий: осталось 5 из 8 · до 20.11 · 💵 не оплачен 200 BYN»."""
    line = (
        f"🎫 {escape(package.title)}: осталось <b>{package.remaining}</b> "
        f"из {package.sessions_total}"
    )
    if package.is_bonus:
        line += " · 🎁 бонус"
    if package.valid_until:
        if package.is_expired(today):
            line += f" · ⌛ истёк {package.valid_until.strftime('%d.%m')}"
        else:
            line += f" · до {package.valid_until.strftime('%d.%m')}"
    if for_trainer and not package.is_paid:
        line += f" · 💵 не оплачен {byn(package.price)}"
    return line


def package_button_label(package: ClientPackage, today: date) -> str:
    if package.status != PackageStatus.ACTIVE:
        icon = "🗄"
    elif package.is_expired(today):
        icon = "⌛"
    else:
        icon = "🎫"
    paid = "" if package.is_paid else " 💵"
    return f"{icon} {package.title} · {package.sessions_used}/{package.sessions_total}{paid}"
