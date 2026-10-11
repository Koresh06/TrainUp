from dataclasses import dataclass

from src.domain.enums.payment import PaymentMethod, PaymentStatus
from src.domain.exception.base import DomainError


@dataclass
class PaymentNotFoundException(DomainError):
    external_id: str

    @property
    def message(self) -> str:
        return f"Платёж {self.external_id} не найден"


@dataclass
class PaymentStatusTransitionException(DomainError):
    external_id: str
    status: PaymentStatus

    @property
    def message(self) -> str:
        return f"Платёж {self.external_id} уже обработан (статус {self.status.value})"


@dataclass
class PaymentProviderNotFoundException(DomainError):
    method: PaymentMethod

    @property
    def message(self) -> str:
        return f"Способ оплаты {self.method.value} не подключён"


@dataclass
class PaymentProviderUnavailableException(DomainError):
    """Платёжная система не ответила (сеть, таймаут, ошибка API) — платёж не
    создан, можно повторить или выбрать другой способ."""

    method: PaymentMethod

    @property
    def message(self) -> str:
        return f"Платёжная система {self.method.value} временно недоступна"


@dataclass
class PaymentAmountInvalidException(DomainError):
    method: PaymentMethod
    reason: str = ""

    @property
    def message(self) -> str:
        return f"Сумма недопустима для {self.method.value}: {self.reason}"
