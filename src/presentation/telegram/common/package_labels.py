from datetime import date
from html import escape

from src.domain.entities.client_package import ClientPackage
from src.domain.enums.package import PackageStatus

PACKAGE_STATUS_TITLES: dict[PackageStatus, str] = {
    PackageStatus.ACTIVE: "активен",
    PackageStatus.FINISHED: "все занятия использованы",
    PackageStatus.CANCELLED: "закрыт",
}


def package_line(package: ClientPackage, today: date) -> str:
    """«🎫 8 занятий: осталось 5 из 8 · до 20.11»."""
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
    return line


def package_button_label(package: ClientPackage, today: date) -> str:
    if package.status != PackageStatus.ACTIVE:
        icon = "🗄"
    elif package.is_expired(today):
        icon = "⌛"
    else:
        icon = "🎫"
    return f"{icon} {package.title} · {package.sessions_used}/{package.sessions_total}"
