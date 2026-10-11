from dataclasses import dataclass

from src.application.services.payment_provider_registry import PaymentProviderRegistry
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.enums.payment import PaymentMethod


@dataclass(frozen=True, eq=False)
class GetPaymentMethodsRequest(UseCaseRequest):
    pass


@dataclass(kw_only=True)
class GetPaymentMethodsUseCase(UseCase[GetPaymentMethodsRequest, list[PaymentMethod]]):
    provider_registry: PaymentProviderRegistry

    async def __call__(self, command: GetPaymentMethodsRequest) -> list[PaymentMethod]:
        return self.provider_registry.available_methods()
