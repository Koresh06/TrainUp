import logging
from dataclasses import dataclass

from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.payment import Payment
from src.domain.enums.payment import PaymentStatus
from src.domain.exception.payment import PaymentNotFoundException
from src.domain.repositories.payment import PaymentRepository
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class RejectPaymentRequest(UseCaseRequest):
    external_id: str
    # True — админ отклонил ручную оплату: тренеру сообщаем; для отмены у
    # провайдера (webhook canceled) тренер и так видит ошибку на странице оплаты
    notify_trainer: bool = False


@dataclass(kw_only=True)
class RejectPaymentUseCase(UseCase[RejectPaymentRequest, Payment]):
    payment_repo: PaymentRepository
    trainer_repo: TrainerRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: RejectPaymentRequest) -> Payment:
        payment = await self.payment_repo.get_by_external_id_for_update(command.external_id)
        if payment is None:
            raise PaymentNotFoundException(command.external_id)
        if payment.status == PaymentStatus.FAILED:
            return payment

        payment.mark_failed()  # оплаченный платёж отклонить нельзя — исключение
        saved = await self.payment_repo.save(payment)
        await self.transaction_manager.commit()

        if command.notify_trainer:
            trainer = await self.trainer_repo.get_by_id(payment.trainer_id)
            if trainer is not None:
                await self.notification_service.send(
                    chat_id=trainer.tg_id,
                    text=(
                        "❌ Администратор не подтвердил оплату подписки.\n"
                        "Если вы уже оплатили — свяжитесь с администратором."
                    ),
                )
        logger.info("[RejectPayment:done] external_id=%s", payment.external_id)
        return saved
