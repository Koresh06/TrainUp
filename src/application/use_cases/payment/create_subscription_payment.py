import logging
import uuid
from dataclasses import dataclass

from src.application.interfaces.notification_service import (
    ManualPaymentRequestDTO,
    NotificationService,
)
from src.application.interfaces.payment_provider import (
    InvoiceRequestDTO,
    PaymentInstructionsDTO,
)
from src.application.services.payment_provider_registry import PaymentProviderRegistry
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.payment._shared import plan_description, usd
from src.application.use_cases.payment.confirm import (
    ConfirmPaymentRequest,
    ConfirmPaymentUseCase,
)
from src.domain.entities.payment import Payment
from src.domain.enums.payment import PaymentMethod, PaymentPurpose, PaymentStatus
from src.domain.exception.subscription import SubscriptionPricePlanNotFoundException
from src.domain.exception.trainer import TrainerNotFoundException
from src.domain.repositories.payment import PaymentRepository
from src.domain.repositories.subscription_price_plan import SubscriptionPricePlanRepository
from src.domain.repositories.trainer import TrainerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreatedPaymentDTO:
    payment: Payment
    instructions: PaymentInstructionsDTO


@dataclass(frozen=True, eq=False)
class CreateSubscriptionPaymentRequest(UseCaseRequest):
    trainer_id: int
    price_plan_id: int
    method: PaymentMethod


@dataclass(kw_only=True)
class CreateSubscriptionPaymentUseCase(
    UseCase[CreateSubscriptionPaymentRequest, CreatedPaymentDTO]
):
    """Счёт на подписку выбранным способом. Логика конкретного способа — в
    стратегии PaymentProvider, здесь только общий сценарий."""

    trainer_repo: TrainerRepository
    price_plan_repo: SubscriptionPricePlanRepository
    payment_repo: PaymentRepository
    provider_registry: PaymentProviderRegistry
    confirm_use_case: ConfirmPaymentUseCase
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: CreateSubscriptionPaymentRequest) -> CreatedPaymentDTO:
        provider = self.provider_registry.get(command.method)

        trainer = await self.trainer_repo.get_by_id(command.trainer_id)
        if trainer is None:
            raise TrainerNotFoundException(trainer_id=command.trainer_id)
        plan = await self.price_plan_repo.get_by_id(command.price_plan_id)
        if plan is None or not plan.is_active:
            raise SubscriptionPricePlanNotFoundException(command.price_plan_id)

        external_id = uuid.uuid4().hex
        description = plan_description(plan)
        provider_meta = await provider.create_invoice(
            InvoiceRequestDTO(
                external_id=external_id,
                amount=plan.price,
                description=description,
                trainer_tg_id=trainer.tg_id,
                trainer_phone=trainer.phone,
            )
        )

        payment = await self.payment_repo.save(
            Payment(
                external_id=external_id,
                trainer_id=trainer.id,
                method=command.method,
                amount=plan.price,
                purpose=PaymentPurpose.SUBSCRIPTION,
                purpose_id=plan.id,
                description=description,
                status=(
                    PaymentStatus.WAITING_CONFIRMATION
                    if provider.requires_admin_confirmation
                    else PaymentStatus.PENDING
                ),
                meta=provider_meta,
            )
        )
        await self.transaction_manager.commit()
        logger.info(
            "[CreateSubscriptionPayment:done] external_id=%s trainer_id=%s method=%s",
            external_id, trainer.id, command.method,
        )

        if provider.requires_admin_confirmation:
            await self.notification_service.notify_manual_payment_request(
                ManualPaymentRequestDTO(
                    external_id=external_id,
                    trainer_name=trainer.name,
                    trainer_tg_id=trainer.tg_id,
                    trainer_phone=trainer.phone,
                    plan_label=description,
                    amount_label=usd(plan.price),
                )
            )
        if provider.confirms_immediately:
            await self.confirm_use_case(ConfirmPaymentRequest(external_id=external_id))
            payment = await self.payment_repo.get_by_external_id(external_id)

        return CreatedPaymentDTO(payment=payment, instructions=provider.get_instructions(payment))
