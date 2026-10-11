from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, ClassVar

from src.domain.entities.payment import Payment
from src.domain.enums.payment import PaymentMethod


@dataclass(frozen=True)
class InvoiceRequestDTO:
    external_id: str
    amount: Decimal          # в базовой валюте (USD)
    description: str
    trainer_tg_id: int
    trainer_phone: str | None = None


@dataclass(frozen=True)
class PaymentInstructionsDTO:
    text: str               # что показать тренеру после создания платежа
    url: str | None = None  # ссылка на оплату (ЮKassa / инвойс Stars)


class PaymentProvider(ABC):
    """
    Стратегия способа оплаты. Новый способ = новый класс-провайдер +
    регистрация в PaymentProviderRegistry (providers/services.py) —
    use case'ы, диалоги и подтверждение платежа не меняются.
    """

    method: ClassVar[PaymentMethod]
    # оплату подтверждает админ вручную (заявка с кнопками в боте)
    requires_admin_confirmation: ClassVar[bool] = False
    # оплата подтверждается сразу после создания (тестовый провайдер)
    confirms_immediately: ClassVar[bool] = False

    @abstractmethod
    async def create_invoice(self, request: InvoiceRequestDTO) -> dict[str, Any]:
        """Создаёт счёт у провайдера; возвращает meta для сохранения в Payment.meta.
        Ошибки сети — PaymentProviderUnavailableException, недопустимая сумма —
        PaymentAmountInvalidException."""
        ...

    @abstractmethod
    def get_instructions(self, payment: Payment) -> PaymentInstructionsDTO: ...
