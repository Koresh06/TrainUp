from typing import Any

from src.application.interfaces.payment_provider import (
    InvoiceRequestDTO,
    PaymentInstructionsDTO,
    PaymentProvider,
)
from src.core.config.payment import ManualPaymentSettings
from src.domain.entities.payment import Payment
from src.domain.enums.payment import PaymentMethod


class ManualPaymentProvider(PaymentProvider):
    """Тренер платит админу напрямую (наличные, перевод, любым удобным способом).
    Админам уходит заявка с кнопками «✅ Оплата получена / ❌ Отклонить»."""

    method = PaymentMethod.MANUAL
    requires_admin_confirmation = True

    def __init__(self, settings: ManualPaymentSettings) -> None:
        self._settings = settings

    async def create_invoice(self, request: InvoiceRequestDTO) -> dict[str, Any]:
        return {"admin_contact": self._settings.admin_contact}

    def get_instructions(self, payment: Payment) -> PaymentInstructionsDTO:
        contact = payment.meta.get("admin_contact")
        contact_line = f"\n📞 Связь с администратором: {contact}" if contact else ""
        return PaymentInstructionsDTO(
            text=(
                f"К оплате: <b>${payment.amount}</b>.\n\n"
                "Заявка отправлена администратору — он свяжется с вами и подскажет, "
                "как оплатить. После подтверждения оплаты подписка активируется "
                f"автоматически, придёт сообщение.{contact_line}"
            ),
        )
