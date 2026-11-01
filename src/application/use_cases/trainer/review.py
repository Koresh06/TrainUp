import logging
from dataclasses import dataclass

from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.trainer._shared import notify_referrer, start_trial
from src.domain.constants import TRAINER_REFERRAL_FRIEND_DAYS, TRAINER_TRIAL_DAYS
from src.domain.entities.trainer import Trainer
from src.domain.enums.trainer import TrainerApprovalStatus
from src.domain.exception.trainer import (
    TrainerAlreadyReviewedException,
    TrainerNotFoundException,
)
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)

TRAINER_REJECTED_TEXT = "❌ <b>Заявка не одобрена.</b>"


@dataclass(frozen=True, eq=False)
class ReviewTrainerRequest(UseCaseRequest):
    trainer_id: int
    approve: bool
    reviewed_by_tg_id: int
    # кнопки уведомления: заявку мог уже решить другой админ, старая кнопка не
    # должна перебить его решение. В админке отклонённого можно одобрить позже
    only_pending: bool = False


@dataclass(kw_only=True)
class ReviewTrainerUseCase(UseCase[ReviewTrainerRequest, Trainer]):
    """Решение по заявке. Пробный период и бонус-уведомление пригласившему — только
    здесь: срок триала идёт с момента, когда тренер реально может работать.
    Строка блокируется FOR UPDATE: два админа одновременно не выдадут триал дважды."""

    trainer_repo: TrainerRepository
    subscription_repo: TrainerSubscriptionRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager
    trial_days: int = TRAINER_TRIAL_DAYS
    referral_friend_days: int = TRAINER_REFERRAL_FRIEND_DAYS

    async def __call__(self, command: ReviewTrainerRequest) -> Trainer:
        trainer = await self.trainer_repo.get_by_id_for_update(command.trainer_id)
        if trainer is None:
            raise TrainerNotFoundException(trainer_id=command.trainer_id)

        target = (
            TrainerApprovalStatus.APPROVED
            if command.approve
            else TrainerApprovalStatus.REJECTED
        )
        if trainer.approval_status == target or (
            command.only_pending
            and trainer.approval_status != TrainerApprovalStatus.PENDING
        ):
            raise TrainerAlreadyReviewedException(trainer_id=trainer.id)
        if trainer.is_approved:
            # одобренный уже работает: отзывать допуск — это блокировка в карточке
            raise TrainerAlreadyReviewedException(trainer_id=trainer.id)

        trainer.approval_status = target
        saved = await self.trainer_repo.save(trainer)

        referrer = None
        trial_days = 0
        if command.approve:
            if trainer.referred_by_trainer_id is not None:
                referrer = await self.trainer_repo.get_by_id(trainer.referred_by_trainer_id)
            trial_days = await start_trial(
                saved,
                has_referrer=referrer is not None,
                subscription_repo=self.subscription_repo,
                trial_days=self.trial_days,
                referral_friend_days=self.referral_friend_days,
            )
        await self.transaction_manager.commit()

        await self.notification_service.send(
            chat_id=saved.tg_id,
            text=self._decision_text(command.approve, trial_days),
        )
        if referrer is not None:
            await notify_referrer(saved, referrer, self.notification_service)

        logger.info(
            "[ReviewTrainer:done] trainer_id=%s status=%s by=%s",
            saved.id, target, command.reviewed_by_tg_id,
        )
        return saved

    def _decision_text(self, approved: bool, trial_days: int) -> str:
        if approved:
            trial = f"🎁 Пробный период: <b>{trial_days} дн.</b>\n" if trial_days else ""
            return f"✅ <b>Заявка одобрена!</b>\n\n{trial}Откройте кабинет: /trainer"
        return TRAINER_REJECTED_TEXT
