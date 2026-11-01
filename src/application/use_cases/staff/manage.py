import logging
from dataclasses import dataclass

from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.bot_admin import BotAdmin
from src.domain.enums.admin import AdminPermission
from src.domain.exception.admin import (
    AdminAlreadyExistsException,
    AdminNotFoundException,
    AdminUserNotFoundException,
)
from src.domain.repositories.bot_admin import BotAdminRepository
from src.domain.repositories.bot_user import BotUserRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class AddAdminRequest(UseCaseRequest):
    added_by_tg_id: int
    tg_id: int | None = None
    username: str | None = None  # без @; ровно одно из двух


@dataclass(kw_only=True)
class AddAdminUseCase(UseCase[AddAdminRequest, BotAdmin]):
    """Новый админ создаётся без прав: супер-админ сам отмечает, что ему можно."""

    admin_repo: BotAdminRepository
    bot_user_repo: BotUserRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager
    super_admin_ids: list[int]

    async def __call__(self, command: AddAdminRequest) -> BotAdmin:
        if command.username is not None:
            bot_user = await self.bot_user_repo.get_by_username(command.username)
            if bot_user is None:
                raise AdminUserNotFoundException(username=command.username)
            tg_id = bot_user.tg_id
        else:
            tg_id = command.tg_id
            bot_user = await self.bot_user_repo.get_by_tg_id(tg_id)

        if tg_id in self.super_admin_ids or await self.admin_repo.get_by_tg_id(tg_id):
            raise AdminAlreadyExistsException(tg_id=tg_id)

        admin = await self.admin_repo.save(
            BotAdmin(
                tg_id=tg_id,
                name=_display_name(bot_user),
                added_by_tg_id=command.added_by_tg_id,
            )
        )
        await self.transaction_manager.commit()
        await self.notification_service.notify_admins(
            [tg_id], "🛠 Вам выдан доступ к админке бота. Откройте её командой /admin"
        )
        logger.info("[AddAdmin:done] tg_id=%s by=%s", tg_id, command.added_by_tg_id)
        return admin


def _display_name(bot_user) -> str | None:
    if bot_user is None:
        return None
    if bot_user.username:
        return f"{bot_user.first_name or ''} @{bot_user.username}".strip()
    return bot_user.first_name


@dataclass(frozen=True, eq=False)
class ToggleAdminPermissionRequest(UseCaseRequest):
    tg_id: int
    permission: AdminPermission


@dataclass(kw_only=True)
class ToggleAdminPermissionUseCase(UseCase[ToggleAdminPermissionRequest, BotAdmin]):
    admin_repo: BotAdminRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: ToggleAdminPermissionRequest) -> BotAdmin:
        admin = await self.admin_repo.get_by_tg_id(command.tg_id)
        if admin is None:
            raise AdminNotFoundException(tg_id=command.tg_id)
        admin.toggle_permission(command.permission)
        saved = await self.admin_repo.save(admin)
        await self.transaction_manager.commit()
        logger.info(
            "[ToggleAdminPermission:done] tg_id=%s permission=%s granted=%s",
            command.tg_id, command.permission, command.permission in saved.permissions,
        )
        return saved


@dataclass(frozen=True, eq=False)
class RemoveAdminRequest(UseCaseRequest):
    tg_id: int


@dataclass(kw_only=True)
class RemoveAdminUseCase(UseCase[RemoveAdminRequest, None]):
    admin_repo: BotAdminRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: RemoveAdminRequest) -> None:
        await self.admin_repo.delete(command.tg_id)
        await self.transaction_manager.commit()
        await self.notification_service.notify_admins(
            [command.tg_id], "🛠 Ваш доступ к админке бота отключён."
        )
        logger.info("[RemoveAdmin:done] tg_id=%s", command.tg_id)
