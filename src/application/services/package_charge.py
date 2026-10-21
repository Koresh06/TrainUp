import logging
from dataclasses import dataclass

from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.package._shared import _notify_low_balance
from src.domain.entities.booking import Booking
from src.domain.enums.booking import BookingStatus
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.client_package import ClientPackageRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.repositories.trainer_booking_settings import TrainerBookingSettingsRepository
from src.domain.utils import get_project_today

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class PackageChargeService:
    """
    Списание занятий с абонемента. Вызывается везде, где меняется «итоговый»
    статус записи (автозавершение, неявка, исправление неявки), чтобы правило
    было одно.
    """

    package_repo: ClientPackageRepository
    booking_settings_repo: TrainerBookingSettingsRepository
    client_repo: ClientRepository
    trainer_repo: TrainerRepository
    notification_service: NotificationService

    async def sync(self, booking: Booking) -> None:
        """
        Проведённая тренировка (и неявка, если так настроил тренер) списывает одно
        занятие, исправление статуса — возвращает. Меняет booking.package_id —
        сохранить запись и закоммитить должен вызывающий.
        """
        settings = await self.booking_settings_repo.get_by_trainer_id(booking.trainer_id)
        no_show_charges = settings.no_show_charges_package if settings is not None else True
        should_charge = booking.status == BookingStatus.COMPLETED or (
            booking.status == BookingStatus.NO_SHOW and no_show_charges
        )

        if not should_charge and booking.package_id is not None:
            package = await self.package_repo.get_by_id(booking.package_id)
            if package is not None:
                package.refund()
                await self.package_repo.save(package)
            booking.package_id = None
            return

        if not should_charge or booking.package_id is not None:
            return

        today = get_project_today()
        candidates = [
            p for p in await self.package_repo.get_by_client(booking.client_id)
            if p.trainer_id == booking.trainer_id and p.can_charge(today)
        ]
        if not candidates:
            return
        # сначала тот, что раньше сгорит, затем — более старый
        package = min(candidates, key=lambda p: (p.valid_until or today.max, p.id))
        package.charge(today)
        await self.package_repo.save(package)
        booking.package_id = package.id
        logger.info(
            "[PackageCharge] booking_id=%s package_id=%s remaining=%s",
            booking.id, package.id, package.remaining,
        )
        await _notify_low_balance(
            package, self.client_repo, self.trainer_repo, self.notification_service
        )
