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
        await self.notification_service.notify_manual_payment_request(
            data, await self._never_lost(AdminNotification.MANUAL_PAYMENT)
        )

    async def notify_trainer_application(
        self, trainer_id: int, text: str, photo_file_id: str | None
    ) -> None:
        await self.notification_service.notify_trainer_application(
            trainer_id=trainer_id,
            text=text,
            photo_file_id=photo_file_id,
            chat_ids=await self._never_lost(AdminNotification.TRAINER_APPLICATION),
        )

    async def _never_lost(self, kind: AdminNotification) -> list[int]:
        # такую заявку нельзя потерять: человек ждёт решения, а принять его больше
        # некому — если все выключили уведомление, она всё равно уйдёт супер-админам
        return await self._recipients(kind) or list(self.super_admin_ids)

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
