from dataclasses import dataclass
import logging
import secrets

from src.application.interfaces.notification_service import NotificationService
from src.application.services.admin_notifier import AdminNotifier
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.trainer._shared import (
    notify_referrer,
    start_trial,
    trainer_application_text,
)
from src.domain.constants import (
    DEFAULT_CALENDAR_HORIZON_DAYS,
    DEFAULT_MAX_ACTIVE_BOOKINGS,
    GOAL_LABELS,
    HEALTH_CONDITION_LABELS,
    TRAINER_REFERRAL_FRIEND_DAYS,
    TRAINER_APPROVAL_REQUIRED,
    TRAINER_TRIAL_DAYS,
)
from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.entities.trainer import Trainer
from src.domain.entities.trainer_booking_settings import TrainerBookingSettings
from src.domain.entities.trainer_invite_link import TrainerInviteLink
from src.domain.enums.question_type import QuestionType
from src.domain.enums.trainer import TrainerApprovalStatus
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
    # пришёл по ссылке «пригласить тренера» другого тренера
    referred_by_trainer_id: int | None = None
    # только для заявки админу, в профиле не хранятся
    username: str | None = None
    group_title: str | None = None


@dataclass(kw_only=True)
class RegisterTrainerUseCase(UseCase[RegisterTrainerRequest, Trainer]):
    trainer_repo: TrainerRepository
    invite_link_repo: TrainerInviteLinkRepository
    booking_settings_repo: TrainerBookingSettingsRepository
    question_repo: RegistrationQuestionRepository
    subscription_repo: TrainerSubscriptionRepository
    notification_service: NotificationService
    admin_notifier: AdminNotifier
    transaction_manager: TransactionManager
    trial_days: int = TRAINER_TRIAL_DAYS  # APP_CONFIG__BUSINESS__TRAINER_TRIAL_DAYS, 0 — без триала
    referral_friend_days: int = TRAINER_REFERRAL_FRIEND_DAYS
    approval_required: bool = TRAINER_APPROVAL_REQUIRED

    async def __call__(self, command: RegisterTrainerRequest) -> Trainer:
        referrer = (
            await self.trainer_repo.get_by_id(command.referred_by_trainer_id)
            if command.referred_by_trainer_id is not None
            else None
        )
        trainer = Trainer(
            tg_id=command.tg_id,
            name=command.name,
            bio=command.bio,
            notification_chat_id=command.notification_chat_id,
            is_active=True,
            photo_file_id=command.photo_file_id,
            phone=command.phone,
            referred_by_trainer_id=referrer.id if referrer is not None else None,
            approval_status=(
                TrainerApprovalStatus.PENDING
                if self.approval_required
                else TrainerApprovalStatus.APPROVED
            ),
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

        # пробный период — сразу, если заявки выключены: тренер успевает настроить
        # расписание и позвать клиентов до решения о покупке. Иначе — при одобрении
        trial_days = 0
        if not self.approval_required:
            trial_days = await start_trial(
                saved_trainer,
                has_referrer=referrer is not None,
                subscription_repo=self.subscription_repo,
                trial_days=self.trial_days,
                referral_friend_days=self.referral_friend_days,
            )

        await self.transaction_manager.commit()

        if self.approval_required:
            await self.admin_notifier.notify_trainer_application(
                trainer_id=saved_trainer.id,
                text=trainer_application_text(
                    saved_trainer, referrer, command.username, command.group_title
                ),
                photo_file_id=saved_trainer.photo_file_id,
            )
        elif referrer is not None:
            await notify_referrer(saved_trainer, referrer, self.notification_service)

        logger.info(
            "[RegisterTrainer:done] trainer_id=%s trial_days=%s referrer_id=%s",
            saved_trainer.id, trial_days, referrer.id if referrer else None,
        )
        return saved_trainer
