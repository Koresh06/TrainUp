import logging
from dataclasses import dataclass
from datetime import timedelta

from src.application.interfaces.booking_scheduler import BookingScheduler
from src.application.interfaces.notification_service import (
    NotificationService,
    RatingRequestDTO,
)
from src.application.services.package_charge import PackageChargeService
from src.application.services.referral_reward import ReferralRewardService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.constants import PLAN_NEXT_TRAINING_REMINDER_DAYS
from src.domain.enums.booking import BookingStatus
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.repositories.trainer_booking_settings import TrainerBookingSettingsRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager
from src.utils.get_datetime_utc_now import get_datetime_utc_now

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class MarkBookingCompletedRequest(UseCaseRequest):
    booking_id: int


@dataclass(kw_only=True)
class MarkBookingCompletedUseCase(UseCase[MarkBookingCompletedRequest, None]):
    booking_repo: BookingRepository
    booking_scheduler: BookingScheduler
    package_charge: PackageChargeService
    referral_reward: ReferralRewardService
    client_repo: ClientRepository
    trainer_repo: TrainerRepository
    slot_repo: CalendarSlotRepository
    booking_settings_repo: TrainerBookingSettingsRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: MarkBookingCompletedRequest) -> None:
        booking = await self.booking_repo.get_by_id(command.booking_id)
        if booking is None or booking.status != BookingStatus.CONFIRMED:
            return

        booking.complete()
        booking.completion_job_id = None
        await self.package_charge.sync(booking)
        await self.booking_repo.save(booking)
        await self.referral_reward.on_completed(booking)
        await self.transaction_manager.commit()

        await self.booking_scheduler.schedule_plan_next_training_reminder(
            client_id=booking.client_id,
            remind_at_utc=get_datetime_utc_now()
            + timedelta(days=PLAN_NEXT_TRAINING_REMINDER_DAYS),
        )
        await self._ask_rating(booking.id, booking.client_id, booking.trainer_id, booking.slot_id)
        logger.info("[MarkBookingCompleted:done] booking_id=%s", booking.id)

    async def _ask_rating(self, booking_id: int, client_id: int, trainer_id: int, slot_id: int) -> None:
        settings = await self.booking_settings_repo.get_by_trainer_id(trainer_id)
        if settings is not None and not settings.ask_rating:
            return
        client = await self.client_repo.get_by_id(client_id)
        trainer = await self.trainer_repo.get_by_id(trainer_id)
        slot = await self.slot_repo.get_by_id(slot_id)
        if client is None or not client.has_telegram or trainer is None or slot is None:
            return
        await self.notification_service.notify_rating_request(
            RatingRequestDTO(
                chat_id=client.tg_id,
                booking_id=booking_id,
                trainer_name=trainer.name,
                date_label=f"{slot.slot_date.strftime('%d.%m')} в {slot.start_time.strftime('%H:%M')}",
            )
        )
