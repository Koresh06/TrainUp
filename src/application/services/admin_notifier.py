from dataclasses import dataclass

from src.application.interfaces.notification_service import (
    ManualPaymentRequestDTO,
    NotificationService,
)
from src.domain.enums.admin import AdminNotification
from src.domain.repositories.bot_admin import BotAdminRepository


@dataclass(kw_only=True)
class AdminNotifier:
    """Решает, кому из админов отправить уведомление: супер-админам и тем, у
    кого есть нужное право, если они не выключили этот тип у себя."""

    admin_repo: BotAdminRepository
    notification_service: NotificationService
    super_admin_ids: list[int]

    async def notify(self, kind: AdminNotification, text: str) -> None:
        recipients = await self._recipients(kind)
        if recipients:
            await self.notification_service.notify_admins(recipients, text)

    async def notify_manual_payment(self, data: ManualPaymentRequestDTO) -> None:
        # заявку нельзя потерять: тренер ждёт подписку, а подтвердить её больше
        # некому — если все выключили уведомление, она всё равно уйдёт супер-админам
        recipients = await self._recipients(AdminNotification.MANUAL_PAYMENT)
        await self.notification_service.notify_manual_payment_request(
            data, recipients or list(self.super_admin_ids)
        )

    async def _recipients(self, kind: AdminNotification) -> list[int]:
        admins = {admin.tg_id: admin for admin in await self.admin_repo.get_all()}
        recipients = [
            tg_id
            for tg_id in self.super_admin_ids
            if tg_id not in admins or kind not in admins[tg_id].muted_notifications
        ]
        recipients += [
            admin.tg_id
            for admin in admins.values()
            if admin.tg_id not in self.super_admin_ids
            and kind.required_permission in admin.permissions
            and kind not in admin.muted_notifications
        ]
        return recipients
