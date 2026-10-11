import logging
from decimal import ROUND_CEILING, Decimal
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import LabeledPrice

from src.application.interfaces.payment_provider import (
    InvoiceRequestDTO,
    PaymentInstructionsDTO,
    PaymentProvider,
)
from src.core.config.payment import TelegramStarsSettings
from src.domain.entities.payment import Payment
from src.domain.enums.payment import PaymentMethod
from src.domain.exception.payment import (
    PaymentAmountInvalidException,
    PaymentProviderUnavailableException,
)

logger = logging.getLogger(__name__)


class TelegramStarsProvider(PaymentProvider):
    """Инвойс в XTR. Оплату подтверждает сам Telegram апдейтом successful_payment
    (payload инвойса == external_id) — см. features/trainer/register/router.py."""

    method = PaymentMethod.TELEGRAM_STARS

    def __init__(self, bot: Bot, settings: TelegramStarsSettings) -> None:
        self._bot = bot
        self._settings = settings

    def to_stars(self, amount_usd: Decimal) -> int:
        return int((amount_usd / self._settings.usd_per_star).to_integral_value(rounding=ROUND_CEILING))

    async def create_invoice(self, request: InvoiceRequestDTO) -> dict[str, Any]:
        stars = self.to_stars(request.amount)
        if stars < 1:
            raise PaymentAmountInvalidException(method=self.method, reason="меньше 1 звезды")

        try:
            invoice_link = await self._bot.create_invoice_link(
                title=request.description[:32],
                description=request.description,
                payload=request.external_id,
                currency="XTR",
                prices=[LabeledPrice(label="XTR", amount=stars)],
            )
        except TelegramBadRequest as error:
            raise PaymentAmountInvalidException(method=self.method, reason=str(error)) from error
        except TelegramAPIError as error:
            logger.exception("[TelegramStars:create_failed] external_id=%s", request.external_id)
            raise PaymentProviderUnavailableException(self.method) from error

        return {
            "invoice_link": invoice_link,
            "stars_amount": stars,
            "usd_per_star": str(self._settings.usd_per_star),
        }

    def get_instructions(self, payment: Payment) -> PaymentInstructionsDTO:
        return PaymentInstructionsDTO(
            text=(
                f"К оплате: <b>{payment.meta.get('stars_amount')} ⭐</b> (${payment.amount}).\n\n"
                "Нажмите «Оплатить» и подтвердите платёж в Telegram — "
                "подписка активируется сразу."
            ),
            url=payment.meta.get("invoice_link"),
        )
