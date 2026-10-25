import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from src.application.interfaces.notification_service import (
    DigestItemDTO,
    NotificationService,
    TrainerDigestDTO,
)
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.constants import PROJECT_TIMEZONE, day_label
from src.domain.entities.trainer import Trainer
from src.domain.entities.trainer_reminder_settings import TrainerReminderSettings
from src.domain.enums.booking import BookingStatus
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.repositories.trainer_reminder_settings import (
    TrainerReminderSettingsRepository,
)
from src.infrastructure.database.transaction_manager.base import TransactionManager
from src.utils.get_datetime_utc_now import get_aware_utc_now

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class SendTrainerDigestsRequest(UseCaseRequest):
    # для тестов — «сейчас» можно подменить
    now: datetime | None = None


@dataclass(kw_only=True)
class SendTrainerDigestsUseCase(UseCase[SendTrainerDigestsRequest, int]):
    """
    Сводка тренеру в личку: утром — «сегодня у вас…», вечером (если включено)
    — «завтра у вас…». Cron запускается каждые 15 минут, а час отправки у
    каждого тренера свой. Дата последней отправки хранится в настройках, поэтому
    повторные запуски в тот же час ничего не дублируют.
    """

    trainer_repo: TrainerRepository
    subscription_repo: TrainerSubscriptionRepository
    settings_repo: TrainerReminderSettingsRepository
    booking_repo: BookingRepository
    client_repo: ClientRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: SendTrainerDigestsRequest) -> int:
        local_now = (command.now or get_aware_utc_now()).astimezone(PROJECT_TIMEZONE)
        sent = 0

        for trainer in await self.trainer_repo.get_all_active():
            try:
                sent += await self._process_trainer(trainer, local_now)
            except Exception:
                # сбой у одного тренера (флуд-лимит, сеть) не должен оставлять
                # без сводки всех следующих по списку
                await self.transaction_manager.rollback()
                logger.exception("[SendTrainerDigests:error] trainer_id=%s", trainer.id)

        logger.info("[SendTrainerDigests:done] hour=%s sent=%s", local_now.hour, sent)
        return sent

    async def _process_trainer(self, trainer: Trainer, local_now: datetime) -> int:
        today = local_now.date()
        sent = 0
        if await self.subscription_repo.get_active_by_trainer_id(trainer.id) is None:
            return 0
        settings = await self.settings_repo.get_by_trainer_id(trainer.id)
        settings = settings or TrainerReminderSettings(trainer_id=trainer.id)

        changed = False
        if (
            settings.morning_digest_hour == local_now.hour
            and settings.last_morning_digest_on != today
        ):
            sent += await self._send(trainer, settings, today, is_tomorrow=False)
            settings.last_morning_digest_on = today
            changed = True
        if (
            settings.evening_digest_hour == local_now.hour
            and settings.last_evening_digest_on != today
        ):
            sent += await self._send(
                trainer, settings, today + timedelta(days=1), is_tomorrow=True
            )
            settings.last_evening_digest_on = today
            changed = True

        if changed:
            await self.settings_repo.save(settings)
            await self.transaction_manager.commit()
        return sent

    async def _send(
        self,
        trainer: Trainer,
        settings: TrainerReminderSettings,
        day: date,
        *,
        is_tomorrow: bool,
    ) -> int:
        views = await self.booking_repo.get_views(
            trainer_id=trainer.id,
            date_from=day,
            date_to=day,
            statuses=(BookingStatus.PENDING, BookingStatus.CONFIRMED),
        )
        pending = await self.booking_repo.get_views(
            trainer_id=trainer.id,
            date_from=day,
            statuses=(BookingStatus.PENDING,),
        )
        if not views and not settings.digest_on_empty_days:
            return 0

        notes = {
            c.id: c.trainer_note
            for c in await self.client_repo.get_by_trainer_id(trainer.id)
            if c.trainer_note
        }
        await self.notification_service.notify_trainer_digest(
            TrainerDigestDTO(
                chat_id=trainer.tg_id,
                day=day,
                day_label=day_label(day),
                is_tomorrow=is_tomorrow,
                items=[
                    DigestItemDTO(
                        time_label=v.start_time.strftime("%H:%M"),
                        client_name=v.client_full_name,
                        is_pending=v.booking.status == BookingStatus.PENDING,
                        is_recurring=v.booking.recurring_booking_id is not None,
                        is_offline=not v.client_has_telegram,
                        trainer_note=notes.get(v.booking.client_id),
                        client_confirmed=v.booking.client_confirmed_at is not None,
                    )
                    for v in views
                ],
                expected_income=sum(
                    (v.booking.price for v in views if v.booking.price), Decimal("0")
                ),
                pending_total=len(pending),
            )
        )
        return 1
