import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from src.application.interfaces.notification_service import (
    NotificationService,
    SubscriptionEvent,
    SubscriptionNotificationDTO,
)
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.constants import SUBSCRIPTION_WARNING_HOURS
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.subscription import SubscriptionStatus
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class CheckExpiringSubscriptionsRequest(UseCaseRequest):
    pass


@dataclass(kw_only=True)
class CheckExpiringSubscriptionsUseCase(UseCase[CheckExpiringSubscriptionsRequest, None]):
    """
    Cron (раз в час). По каждому тренеру смотрим самую длинную активную подписку:
      - до окончания осталось ≤ SUBSCRIPTION_WARNING_HOURS[i] — предупреждение
        (каждый порог — один раз, отмечаем в notified_stage);
      - срок вышел — статус EXPIRED и уведомление с кнопкой продления.
    Перекрытые продлением старые подписки помечаются EXPIRED молча.
    """

    subscription_repo: TrainerSubscriptionRepository
    trainer_repo: TrainerRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: CheckExpiringSubscriptionsRequest) -> None:
        now = datetime.now(timezone.utc)
        active = await self.subscription_repo.get_all_by_status(SubscriptionStatus.ACTIVE)

        by_trainer: dict[int, list[TrainerSubscription]] = {}
        for subscription in active:
            by_trainer.setdefault(subscription.trainer_id, []).append(subscription)

        warned = expired = 0
        for trainer_id, subscriptions in by_trainer.items():
            subscriptions.sort(key=lambda s: s.expired_at)
            latest = subscriptions[-1]

            for old in subscriptions[:-1]:
                if old.expired_at <= now:
                    old.expired()
                    await self.subscription_repo.save(old)

            trainer = await self.trainer_repo.get_by_id(trainer_id)
            if latest.expired_at <= now:
                latest.expired()
                latest.notified_stage = len(SUBSCRIPTION_WARNING_HOURS) + 1
                await self.subscription_repo.save(latest)
                await self.transaction_manager.commit()
                if trainer is not None:
                    await self._notify(trainer.tg_id, SubscriptionEvent.EXPIRED, latest, now)
                expired += 1
                continue

            stage = self._warning_stage(latest.expired_at - now)
            if stage > latest.notified_stage:
                latest.notified_stage = stage
                await self.subscription_repo.save(latest)
                await self.transaction_manager.commit()
                if trainer is not None:
                    await self._notify(trainer.tg_id, SubscriptionEvent.WARNING, latest, now)
                warned += 1

        await self.transaction_manager.commit()
        logger.info(
            "[CheckExpiringSubscriptions:done] trainers=%s warned=%s expired=%s",
            len(by_trainer), warned, expired,
        )

    @staticmethod
    def _warning_stage(time_left: timedelta) -> int:
        """Сколько порогов предупреждения уже пройдено (0 — ещё рано)."""
        hours_left = time_left.total_seconds() / 3600
        return sum(1 for hours in SUBSCRIPTION_WARNING_HOURS if hours_left <= hours)

    async def _notify(
        self,
        chat_id: int,
        event: SubscriptionEvent,
        subscription: TrainerSubscription,
        now: datetime,
    ) -> None:
        await self.notification_service.notify_subscription(
            SubscriptionNotificationDTO(
                chat_id=chat_id,
                event=event,
                expired_at=subscription.expired_at,
                hours_left=max(int((subscription.expired_at - now).total_seconds() // 3600), 0),
            )
        )
