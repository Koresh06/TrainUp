from dataclasses import dataclass
import logging
import secrets

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.constants import DEFAULT_CALENDAR_HORIZON_DAYS, DEFAULT_MAX_ACTIVE_BOOKINGS
from src.domain.entities.trainer import Trainer
from src.domain.entities.trainer_booking_settings import TrainerBookingSettings
from src.domain.entities.trainer_invite_link import TrainerInviteLink
from src.domain.repositories.invite_link import TrainerInviteLinkRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.repositories.trainer_booking_settings import TrainerBookingSettingsRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class RegisterTrainerRequest(UseCaseRequest):
    tg_id: int
    name: str
    bio: str
    notification_chat_id: int
    photo_file_id: str | None = None


@dataclass(kw_only=True)
class RegisterTrainerUseCase(UseCase[RegisterTrainerRequest, Trainer]):
    trainer_repo: TrainerRepository
    invite_link_repo: TrainerInviteLinkRepository
    booking_settings_repo: TrainerBookingSettingsRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: RegisterTrainerRequest) -> Trainer:
        trainer = Trainer(
            tg_id=command.tg_id,
            name=command.name,
            bio=command.bio,
            notification_chat_id=command.notification_chat_id,
            is_active=True,
            photo_file_id=command.photo_file_id,
        )
        saved_trainer = await self.trainer_repo.save(trainer)

        invite_link = TrainerInviteLink(
            trainer_id=saved_trainer.id,
            token=secrets.token_urlsafe(16),
            is_active=True,
        )
        await self.invite_link_repo.save(invite_link)

        booking_settings = TrainerBookingSettings(
            trainer_id=saved_trainer.id,
            calendar_horizon_days=DEFAULT_CALENDAR_HORIZON_DAYS,
            max_active_bookings_per_client=DEFAULT_MAX_ACTIVE_BOOKINGS,
        )
        await self.booking_settings_repo.save(booking_settings)

        await self.transaction_manager.commit()

        logger.info("[RegisterTrainer:done] trainer_id=%s", saved_trainer.id)
        return saved_trainer