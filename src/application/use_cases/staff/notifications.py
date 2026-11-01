from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.bot_admin import BotAdmin
from src.domain.enums.admin import AdminNotification
from src.domain.repositories.bot_admin import BotAdminRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class GetMutedNotificationsRequest(UseCaseRequest):
    tg_id: int


@dataclass(kw_only=True)
class GetMutedNotificationsUseCase(
    UseCase[GetMutedNotificationsRequest, set[AdminNotification]]
):
    admin_repo: BotAdminRepository

    async def __call__(
        self, command: GetMutedNotificationsRequest
    ) -> set[AdminNotification]:
        admin = await self.admin_repo.get_by_tg_id(command.tg_id)
        return admin.muted_notifications if admin is not None else set()


@dataclass(frozen=True, eq=False)
class ToggleAdminNotificationRequest(UseCaseRequest):
    tg_id: int
    kind: AdminNotification


@dataclass(kw_only=True)
class ToggleAdminNotificationUseCase(UseCase[ToggleAdminNotificationRequest, None]):
    admin_repo: BotAdminRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: ToggleAdminNotificationRequest) -> None:
        # у супер-админа строки может ещё не быть — появится при первой настройке
        admin = await self.admin_repo.get_by_tg_id(command.tg_id)
        admin = admin or BotAdmin(tg_id=command.tg_id)
        admin.toggle_notification(command.kind)
        await self.admin_repo.save(admin)
        await self.transaction_manager.commit()
