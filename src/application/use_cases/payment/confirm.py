import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from src.application.interfaces.notification_service import (
    NotificationService,
    SubscriptionEvent,
    SubscriptionNotificationDTO,
)
from src.application.services.trainer_referral_reward import TrainerReferralRewardService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.payment._shared import usd
from src.application.use_cases.subscription._shared import _activate_subscription
from src.domain.entities.payment import Payment
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.payment import PaymentMethod, PaymentPurpose, PaymentStatus
from src.domain.enums.subscription import SubscriptionSource
from src.domain.exception.payment import (
    PaymentNotFoundException,
    PaymentStatusTransitionException,
)
from src.domain.exception.subscription import SubscriptionPricePlanNotFoundException
from src.domain.repositories.payment import PaymentRepository
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.subscription_price_plan import SubscriptionPricePlanRepository
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class ConfirmPaymentRequest(UseCaseRequest):
    external_id: str


@dataclass(kw_only=True)
class ConfirmPaymentUseCase(UseCase[ConfirmPaymentRequest, Payment]):
    """
    Общее подтверждение для всех способов (webhook ЮKassa, successful_payment
    Stars, кнопка админа). Идемпотентно: повтор webhook'а или двойное нажатие
    не выдадут подписку дважды — строка платежа блокируется FOR UPDATE.
    """

    payment_repo: PaymentRepository
    price_plan_repo: SubscriptionPricePlanRepository
    subscription_repo: TrainerSubscriptionRepository
    trainer_repo: TrainerRepository
    notification_service: NotificationService
    referral_reward: TrainerReferralRewardService
    transaction_manager: TransactionManager

    async def __call__(self, command: ConfirmPaymentRequest) -> Payment:
        payment = await self.payment_repo.get_by_external_id_for_update(command.external_id)
        if payment is None:
            raise PaymentNotFoundException(command.external_id)
        if payment.status == PaymentStatus.PAID:
            logger.info("[ConfirmPayment:already_paid] external_id=%s", payment.external_id)
            return payment
        if payment.status == PaymentStatus.FAILED:
            raise PaymentStatusTransitionException(
                external_id=payment.external_id, status=payment.status
            )

        payment.mark_paid(datetime.now(timezone.utc))
        saved = await self.payment_repo.save(payment)
        subscription = await self._apply_purpose(payment)
        await self.referral_reward.on_paid(payment.trainer_id)
        await self.transaction_manager.commit()

        trainer = await self.trainer_repo.get_by_id(payment.trainer_id)
        if trainer is not None:
            await self.notification_service.notify_subscription(
                SubscriptionNotificationDTO(
                    chat_id=trainer.tg_id,
                    event=SubscriptionEvent.PAID,
                    expired_at=subscription.expired_at,
                )
            )
            await self.notification_service.notify_admins(
                f"💸 <b>Оплата подписки</b>\n\n"
                f"👤 {trainer.name} (<code>{trainer.tg_id}</code>)\n"
                f"{payment.description or ''}\n"
                f"💰 {usd(payment.amount)} · {payment.method.label()}\n"
                f"🧾 <code>{payment.external_id}</code>"
            )

        logger.info("[ConfirmPayment:done] external_id=%s", payment.external_id)
        return saved

    async def _apply_purpose(self, payment: Payment) -> TrainerSubscription:
        match payment.purpose:
            case PaymentPurpose.SUBSCRIPTION:
                plan = await self.price_plan_repo.get_by_id(payment.purpose_id)
                if plan is None:
                    raise SubscriptionPricePlanNotFoundException(payment.purpose_id)
                return await _activate_subscription(
                    subscription_repo=self.subscription_repo,
                    trainer_id=payment.trainer_id,
                    plan=plan.plan,
                    amount=payment.amount,
                    # ручную оплату админ принял наличными/переводом
                    source=(
                        SubscriptionSource.CASH
                        if payment.method == PaymentMethod.MANUAL
                        else SubscriptionSource.PURCHASE
                    ),
                    months=plan.months,
                )
        raise ValueError(f"Unsupported payment purpose: {payment.purpose}")


