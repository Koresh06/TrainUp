import logging
from dataclasses import dataclass
from decimal import Decimal
from html import escape

from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.subscription._shared import _activate_subscription
from src.domain.constants import TRAINER_REFERRAL_BONUS_DAYS
from src.domain.enums.subscription import SubscriptionPlan, SubscriptionSource
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.trainer import TrainerRepository
from src.utils.get_datetime_utc_now import get_aware_utc_now
from src.utils.timezone import to_moscow

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class TrainerReferralRewardService:
    """
    Реферальная программа тренеров: когда приглашённый тренер впервые оплатил
    подписку (в боте или наличными через админа), пригласившему добавляются
    бесплатные дни подписки. Один раз за каждого приглашённого.
    Commit — на вызывающем (вызывается внутри транзакции оплаты).
    """

    trainer_repo: TrainerRepository
    subscription_repo: TrainerSubscriptionRepository
    notification_service: NotificationService
    bonus_days: int = TRAINER_REFERRAL_BONUS_DAYS

    async def on_paid(self, trainer_id: int) -> None:
        friend = await self.trainer_repo.get_by_id(trainer_id)
        if (
            friend is None
            or friend.referred_by_trainer_id is None
            or friend.referral_rewarded_at is not None
        ):
            return
        friend.referral_rewarded_at = get_aware_utc_now()
        await self.trainer_repo.save(friend)

        referrer = await self.trainer_repo.get_by_id(friend.referred_by_trainer_id)
        if referrer is None or self.bonus_days <= 0:
            return
        bonus = await _activate_subscription(
            subscription_repo=self.subscription_repo,
            trainer_id=referrer.id,
            plan=SubscriptionPlan.CUSTOM,
            amount=Decimal("0"),
            source=SubscriptionSource.REFERRAL,
            days=self.bonus_days,
        )
        logger.info(
            "[TrainerReferralReward] referrer_id=%s friend_id=%s days=%s",
            referrer.id, friend.id, self.bonus_days,
        )
        await self.notification_service.send(
            chat_id=referrer.tg_id,
            text=(
                f"🎁 <b>{escape(friend.name)}</b> оформил подписку по вашему приглашению — "
                f"вам начислено <b>+{self.bonus_days} дней</b> подписки бесплатно.\n"
                f"Подписка действует до {to_moscow(bonus.expired_at).strftime('%d.%m.%Y')}."
            ),
        )
