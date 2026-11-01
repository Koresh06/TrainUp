from dataclasses import dataclass, field

from src.domain.entities.base import Entity
from src.domain.enums.admin import AdminNotification, AdminPermission

# право управлять подразумевает право смотреть — иначе раздел не открыть
IMPLIED_BY: dict[AdminPermission, AdminPermission] = {
    AdminPermission.TRAINERS_VIEW: AdminPermission.TRAINERS_MANAGE,
    AdminPermission.CLIENTS_VIEW: AdminPermission.CLIENTS_MANAGE,
}


@dataclass(kw_only=True)
class BotAdmin(Entity):
    """Строка есть у обычных админов и у супер-админа, который менял настройки
    уведомлений. Супер-админство в таблице не хранится — только ADMIN_IDS."""

    tg_id: int
    name: str | None = None
    permissions: set[AdminPermission] = field(default_factory=set)
    muted_notifications: set[AdminNotification] = field(default_factory=set)
    added_by_tg_id: int | None = None

    @property
    def title(self) -> str:
        return self.name or str(self.tg_id)

    def toggle_permission(self, permission: AdminPermission) -> None:
        self.permissions ^= {permission}

    def toggle_notification(self, kind: AdminNotification) -> None:
        self.muted_notifications ^= {kind}


@dataclass(frozen=True)
class AdminAccess:
    """Права того, кто сейчас нажал кнопку: проверяются на каждом апдейте,
    поэтому отозванное право перестаёт работать сразу, даже в открытом окне."""

    tg_id: int
    is_super: bool
    permissions: frozenset[AdminPermission] = frozenset()

    def can(self, *permissions: AdminPermission) -> bool:
        """Хватает любого из перечисленных прав."""
        return self.is_super or any(self._has(p) for p in permissions)

    def _has(self, permission: AdminPermission) -> bool:
        return (
            permission in self.permissions
            or IMPLIED_BY.get(permission) in self.permissions
        )
