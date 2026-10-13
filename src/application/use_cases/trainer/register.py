from dataclasses import dataclass
from decimal import Decimal
import logging
import secrets

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.subscription._shared import _activate_subscription
from src.domain.constants import (
    DEFAULT_CALENDAR_HORIZON_DAYS,
    DEFAULT_MAX_ACTIVE_BOOKINGS,
    GOAL_LABELS,
    HEALTH_CONDITION_LABELS,
    TRAINER_TRIAL_DAYS,
)
from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.entities.trainer import Trainer
from src.domain.entities.trainer_booking_settings import TrainerBookingSettings
from src.domain.entities.trainer_invite_link import TrainerInviteLink
from src.domain.enums.question_type import QuestionType
from src.domain.enums.subscription import SubscriptionPlan, SubscriptionSource
from src.domain.repositories.invite_link import TrainerInviteLinkRepository
from src.domain.repositories.registration_question import RegistrationQuestionRepository
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.repositories.trainer_booking_settings import (
    TrainerBookingSettingsRepository,
)
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class RegisterTrainerRequest(UseCaseRequest):
    tg_id: int
    name: str
    bio: str
    notification_chat_id: int
    photo_file_id: str | None = None
    phone: str | None = None


@dataclass(kw_only=True)
class RegisterTrainerUseCase(UseCase[RegisterTrainerRequest, Trainer]):
    trainer_repo: TrainerRepository
    invite_link_repo: TrainerInviteLinkRepository
    booking_settings_repo: TrainerBookingSettingsRepository
    question_repo: RegistrationQuestionRepository
    subscription_repo: TrainerSubscriptionRepository
    transaction_manager: TransactionManager
    trial_days: int = TRAINER_TRIAL_DAYS  # APP_CONFIG__BUSINESS__TRAINER_TRIAL_DAYS, 0 — без триала

    async def __call__(self, command: RegisterTrainerRequest) -> Trainer:
        trainer = Trainer(
            tg_id=command.tg_id,
            name=command.name,
            bio=command.bio,
            notification_chat_id=command.notification_chat_id,
            is_active=True,
            photo_file_id=command.photo_file_id,
            phone=command.phone,
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

        await self.question_repo.save(
            RegistrationQuestion(
                trainer_id=saved_trainer.id,
                question_type=QuestionType.MULTI_SELECT,
                label="Ваше состояние здоровья и тела",
                options=list(HEALTH_CONDITION_LABELS.values()),
                order=0,
                is_system=True,
                system_key="health_conditions",
            )
        )
        await self.question_repo.save(
            RegistrationQuestion(
                trainer_id=saved_trainer.id,
                question_type=QuestionType.MULTI_SELECT,
                label="Предпочтения в тренировке",
                options=list(GOAL_LABELS.values()),
                order=1,
                is_system=True,
                system_key="goals",
            )
        )

        # пробный период — сразу при регистрации, чтобы тренер успел настроить
        # расписание и позвать клиентов до решения о покупке. Регистрация
        # одна на tg_id, так что повторно триал не получить
        if self.trial_days > 0:
            await _activate_subscription(
                subscription_repo=self.subscription_repo,
                trainer_id=saved_trainer.id,
                plan=SubscriptionPlan.CUSTOM,
                amount=Decimal("0"),
                source=SubscriptionSource.TRIAL,
                days=self.trial_days,
            )

        await self.transaction_manager.commit()

        logger.info(
            "[RegisterTrainer:done] trainer_id=%s trial_days=%s",
            saved_trainer.id, self.trial_days,
        )
        return saved_trainer
