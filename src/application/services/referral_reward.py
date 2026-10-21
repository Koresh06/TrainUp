import logging
from dataclasses import dataclass
from datetime import timedelta
from html import escape

from src.application.interfaces.notification_service import NotificationService
from src.domain.entities.booking import Booking
from src.domain.entities.client_package import ClientPackage
from src.domain.enums.booking import BookingStatus
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.client_package import ClientPackageRepository
from src.domain.repositories.trainer_booking_settings import TrainerBookingSettingsRepository
from src.domain.utils import get_project_today
from src.utils.get_datetime_utc_now import get_aware_utc_now

logger = logging.getLogger(__name__)

# сколько действуют бонусные занятия за приглашённого друга
REFERRAL_BONUS_VALID_DAYS = 90


@dataclass(kw_only=True)
class ReferralRewardService:
    """
    Реферальная программа: когда приглашённый клиент сходил на первую
    тренировку, пригласившему начисляются бесплатные занятия (бонусный
    абонемент) — сколько, решает тренер в настройках. Награда — один раз
    за каждого друга.
    """

    client_repo: ClientRepository
    package_repo: ClientPackageRepository
    booking_settings_repo: TrainerBookingSettingsRepository
    notification_service: NotificationService

    async def on_completed(self, booking: Booking) -> None:
        if booking.status != BookingStatus.COMPLETED:
            return
        friend = await self.client_repo.get_by_id(booking.client_id)
        if (
            friend is None
            or friend.referred_by_client_id is None
            or friend.referral_rewarded_at is not None
        ):
            return
        friend.referral_rewarded_at = get_aware_utc_now()
        await self.client_repo.save(friend)

        settings = await self.booking_settings_repo.get_by_trainer_id(friend.trainer_id)
        bonus = settings.referral_bonus_sessions if settings else 0
        referrer = await self.client_repo.get_by_id(friend.referred_by_client_id)
        if bonus <= 0 or referrer is None:
            return

        await self.package_repo.save(
            ClientPackage(
                trainer_id=referrer.trainer_id,
                client_id=referrer.id,
                title=f"🎁 Бонус за {friend.first_name}",
                sessions_total=bonus,
                valid_until=get_project_today() + timedelta(days=REFERRAL_BONUS_VALID_DAYS),
                is_bonus=True,
            )
        )
        logger.info("[ReferralReward] referrer_id=%s friend_id=%s bonus=%s", referrer.id, friend.id, bonus)
        if referrer.has_telegram:
            await self.notification_service.send(
                chat_id=referrer.tg_id,
                text=(
                    f"🎁 Ваш друг <b>{escape(friend.full_name)}</b> сходил на первую тренировку — "
                    f"вам начислено бесплатных занятий: <b>{bonus}</b>. "
                    f"Они спишутся автоматически на ближайших тренировках."
                ),
            )
