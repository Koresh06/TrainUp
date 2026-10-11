import asyncio
import logging
import re
import uuid
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from yookassa import Configuration, Payment as YooKassaPayment
from yookassa.client import ApiClient
from yookassa.domain.response import PaymentResponse

from src.application.interfaces.payment_provider import (
    InvoiceRequestDTO,
    PaymentInstructionsDTO,
    PaymentProvider,
)
from src.core.config.payment import YooKassaSettings
from src.domain.entities.payment import Payment
from src.domain.enums.payment import PaymentMethod
from src.domain.exception.payment import (
    PaymentAmountInvalidException,
    PaymentProviderUnavailableException,
)

logger = logging.getLogger(__name__)

YOOKASSA_TIMEOUT_SECONDS = 15
_ORIGINAL_GET_SESSION = ApiClient.get_session


def _route_yookassa_http(proxy: str | None) -> None:
    """SDK ЮKassa берёт прокси из HTTP(S)_PROXY окружения (trust_env=True).
    Ходим в API напрямую, а прокси — только если он явно задан в настройках."""

    def get_session(client: ApiClient):
        session = _ORIGINAL_GET_SESSION(client)
        session.trust_env = False
        session.proxies = {"https": proxy, "http": proxy} if proxy else {}
        return session

    ApiClient.get_session = get_session  # type: ignore[method-assign]


class YooKassaProvider(PaymentProvider):
    method = PaymentMethod.YOOKASSA

    def __init__(self, settings: YooKassaSettings) -> None:
        self._settings = settings
        Configuration.account_id = settings.account_id
        Configuration.secret_key = settings.secret_key
        _route_yookassa_http(settings.proxy or None)

    def to_rub(self, amount_usd: Decimal) -> Decimal:
        return (amount_usd * self._settings.usd_to_rub_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    async def create_invoice(self, request: InvoiceRequestDTO) -> dict[str, Any]:
        amount_rub = self.to_rub(request.amount)
        if amount_rub <= 0:
            raise PaymentAmountInvalidException(method=self.method, reason="сумма ≤ 0")

        payload: dict[str, Any] = {
            "amount": {"value": f"{amount_rub:.2f}", "currency": "RUB"},
            "confirmation": {
                "type": "redirect",
                "return_url": f"{self._settings.return_url}?external_id={request.external_id}",
            },
            "capture": True,
            "description": request.description[:128],
            "metadata": {
                "external_id": request.external_id,
                "trainer_tg_id": request.trainer_tg_id,
            },
        }
        phone = re.sub(r"\D", "", request.trainer_phone or "")
        if phone:
            # чек 54-ФЗ: без НДС, услуга, полная оплата
            payload["receipt"] = {
                "customer": {"phone": phone},
                "items": [
                    {
                        "description": request.description[:128],
                        "quantity": "1.00",
                        "amount": {"value": f"{amount_rub:.2f}", "currency": "RUB"},
                        "vat_code": 1,
                        "payment_mode": "full_payment",
                        "payment_subject": "service",
                    }
                ],
            }

        try:
            response: PaymentResponse = await asyncio.wait_for(
                asyncio.to_thread(YooKassaPayment.create, payload, str(uuid.uuid4())),
                timeout=YOOKASSA_TIMEOUT_SECONDS,
            )
        except Exception as error:
            # сетевые сбои SDK всплывают невнятно — любая ошибка = провайдер недоступен
            logger.exception("[YooKassa:create_failed] external_id=%s", request.external_id)
            raise PaymentProviderUnavailableException(self.method) from error

        return {
            "yookassa_payment_id": response.id,
            "confirmation_url": response.confirmation.confirmation_url,
            "amount_rub": f"{amount_rub:.2f}",
            "usd_to_rub_rate": str(self._settings.usd_to_rub_rate),
        }

    def get_instructions(self, payment: Payment) -> PaymentInstructionsDTO:
        return PaymentInstructionsDTO(
            text=(
                f"К оплате: <b>{payment.meta.get('amount_rub')} ₽</b> "
                f"(${payment.amount} по курсу {payment.meta.get('usd_to_rub_rate')}).\n\n"
                "Нажмите «Оплатить» — откроется страница ЮKassa. После оплаты "
                "подписка активируется автоматически, придёт сообщение."
            ),
            url=payment.meta.get("confirmation_url"),
        )

    async def verify_payment(self, yookassa_payment_id: str) -> PaymentResponse | None:
        """Сверка статуса напрямую в API ЮKassa (по нашему secret_key). Тело
        webhook'а ЮKassa не подписывает — доверять ему нельзя: кто угодно мог бы
        прислать {"event": "payment.succeeded"} со своим payment_id."""
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(YooKassaPayment.find_one, yookassa_payment_id),
                timeout=YOOKASSA_TIMEOUT_SECONDS,
            )
        except Exception:
            logger.exception("[YooKassa:verify_failed] payment_id=%s", yookassa_payment_id)
            return None
