from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.domain.entities.base import Entity
from src.domain.enums.package import PackageStatus
from src.domain.exception.package import PackageNotChargeableException


@dataclass(kw_only=True)
class ClientPackage(Entity):
    """
    Абонемент клиента: N занятий у тренера. Проведённая тренировка (и неявка,
    если так настроил тренер) списывает одно занятие. Оплату бот не ведёт —
    деньги идут мимо бота (наличные/перевод), цена только для статистики.
    """

    trainer_id: int
    client_id: int
    title: str
    sessions_total: int
    sessions_used: int = 0
    price: Decimal | None = None
    valid_until: date | None = None
    status: PackageStatus = PackageStatus.ACTIVE
    # бонусные занятия (например, за приглашённого друга) — не оплачиваются
    is_bonus: bool = False

    @property
    def remaining(self) -> int:
        return max(self.sessions_total - self.sessions_used, 0)

    def is_expired(self, today: date) -> bool:
        return self.valid_until is not None and today > self.valid_until

    def can_charge(self, today: date) -> bool:
        return (
            self.status == PackageStatus.ACTIVE
            and self.remaining > 0
            and not self.is_expired(today)
        )

    def charge(self, today: date) -> None:
        if not self.can_charge(today):
            raise PackageNotChargeableException(package_id=self.id)
        self.sessions_used += 1
        if self.remaining == 0:
            self.status = PackageStatus.FINISHED
        self.touch()

    def refund(self) -> None:
        """Списание отменили (тренер исправил неявку и т.п.) — занятие возвращается."""
        if self.sessions_used == 0:
            return
        self.sessions_used -= 1
        if self.status == PackageStatus.FINISHED:
            self.status = PackageStatus.ACTIVE
        self.touch()

    def cancel(self) -> None:
        self.status = PackageStatus.CANCELLED
        self.touch()
