from typing import Any

from src.application.interfaces.payment_provider import (
    InvoiceRequestDTO,
    PaymentInstructionsDTO,
    PaymentProvider,
)
from src.domain.entities.payment import Payment
from src.domain.enums.payment import PaymentMethod


class TestPaymentProvider(PaymentProvider):
    """Только для разработки (APP_CONFIG__PAYMENT__TEST_MODE=True): платёж
    подтверждается сразу, без денег. В проде не регистрируется."""

    __test__ = False  # не путать pytest
    method = PaymentMethod.TEST
    confirms_immediately = True

    async def create_invoice(self, request: InvoiceRequestDTO) -> dict[str, Any]:
        return {}

    def get_instructions(self, payment: Payment) -> PaymentInstructionsDTO:
        return PaymentInstructionsDTO(text="🧪 Тестовая оплата проведена — подписка активна.")
