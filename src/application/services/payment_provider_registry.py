from src.application.interfaces.payment_provider import PaymentProvider
from src.domain.enums.payment import PaymentMethod
from src.domain.exception.payment import PaymentProviderNotFoundException


class PaymentProviderRegistry:
    """Реестр стратегий оплаты: какие способы подключены — то и видит тренер."""

    def __init__(self) -> None:
        self._providers: dict[PaymentMethod, PaymentProvider] = {}

    def register(self, provider: PaymentProvider) -> None:
        self._providers[provider.method] = provider

    def get(self, method: PaymentMethod) -> PaymentProvider:
        provider = self._providers.get(method)
        if provider is None:
            raise PaymentProviderNotFoundException(method)
        return provider

    def available_methods(self) -> list[PaymentMethod]:
        return list(self._providers)
