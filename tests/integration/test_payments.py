"""Платежи: стратегии провайдеров + общий сценарий создания/подтверждения на
реальной БД. Реестр провайдеров подменён набором фейков-стратегий."""

from types import SimpleNamespace

import pytest
from dishka import Provider, Scope, make_async_container, provide

from src.application.interfaces.payment_provider import (
    InvoiceRequestDTO,
    PaymentInstructionsDTO,
    PaymentProvider,
)
from src.application.mediator import Mediator
from src.application.services.payment_provider_registry import PaymentProviderRegistry
from src.application.use_cases.access.get_user_access import GetUserAccessRequest
from src.application.use_cases.payment.confirm import ConfirmPaymentRequest
from src.application.use_cases.payment.create_subscription_payment import (
    CreateSubscriptionPaymentRequest,
)
from src.application.use_cases.payment.get_by_external_id import (
    GetPaymentByExternalIdRequest,
)
from src.application.use_cases.payment.get_methods import GetPaymentMethodsRequest
from src.application.use_cases.payment.reject import RejectPaymentRequest
from src.application.use_cases.subscription.get_active_price_plans import (
    GetActivePricePlansRequest,
)
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.core.dependencies.providers import make_base_providers
from src.domain.entities.payment import Payment
from src.domain.enums.payment import PaymentMethod, PaymentStatus
from src.domain.enums.subscription import SubscriptionSource
from src.domain.exception.payment import (
    PaymentProviderNotFoundException,
    PaymentStatusTransitionException,
)
from src.infrastructure.database.seed import seed_subscription_price_plans
from src.infrastructure.payment.providers.manual import ManualPaymentProvider
from src.infrastructure.payment.providers.test import TestPaymentProvider
from tests.conftest import FakeExternalsProvider


class FakeLinkProvider(PaymentProvider):
    """Стратегия «оплата по ссылке» (как ЮKassa/Stars) без внешнего API."""

    method = PaymentMethod.YOOKASSA

    def __init__(self) -> None:
        self.requests: list[InvoiceRequestDTO] = []

    async def create_invoice(self, request: InvoiceRequestDTO) -> dict:
        self.requests.append(request)
        return {"confirmation_url": f"https://pay.example/{request.external_id}"}

    def get_instructions(self, payment: Payment) -> PaymentInstructionsDTO:
        return PaymentInstructionsDTO(text="pay", url=payment.meta["confirmation_url"])


class RegistryProvider(Provider):
    def __init__(self, registry: PaymentProviderRegistry) -> None:
        super().__init__()
        self._registry = registry

    @provide(scope=Scope.APP, override=True)
    def registry(self) -> PaymentProviderRegistry:
        return self._registry


@pytest.fixture
def link_provider() -> FakeLinkProvider:
    return FakeLinkProvider()


@pytest.fixture
async def run(app_session_maker, notifications, task_queue, link_provider):
    registry = PaymentProviderRegistry()
    registry.register(link_provider)
    registry.register(ManualPaymentProvider(SimpleNamespace(admin_contact="@boss")))
    registry.register(TestPaymentProvider())
    container = make_async_container(
        *make_base_providers(),
        FakeExternalsProvider(notifications, task_queue),
        RegistryProvider(registry),
    )
    await seed_subscription_price_plans(container)

    async def _run(request):
        async with container() as request_container:
            return await (await request_container.get(Mediator)).handle(request)

    yield _run
    await container.close()


async def _trainer_and_plan(run):
    trainer = await run(
        RegisterTrainerRequest(tg_id=1001, name="Иван", bio="", notification_chat_id=-1, phone="+375291112233")
    )
    plans = await run(GetActivePricePlansRequest())
    return trainer, plans[0]


async def test_available_methods_come_from_registry(run) -> None:
    methods = await run(GetPaymentMethodsRequest())
    assert methods == [PaymentMethod.YOOKASSA, PaymentMethod.MANUAL, PaymentMethod.TEST]


async def test_link_payment_confirmed_once(run, link_provider, notifications) -> None:
    trainer, plan = await _trainer_and_plan(run)
    created = await run(
        CreateSubscriptionPaymentRequest(trainer_id=trainer.id, price_plan_id=plan.id, method=PaymentMethod.YOOKASSA)
    )
    payment = created.payment
    assert payment.status == PaymentStatus.PENDING
    assert payment.amount == plan.price and payment.currency == "USD"
    assert created.instructions.url.endswith(payment.external_id)
    assert link_provider.requests[0].trainer_phone == "+375291112233"
    assert not (await run(GetUserAccessRequest(tg_id=trainer.tg_id))).trainer_subscription_active

    # webhook пришёл дважды — подписка выдаётся один раз
    await run(ConfirmPaymentRequest(external_id=payment.external_id))
    await run(ConfirmPaymentRequest(external_id=payment.external_id))

    stored = await run(GetPaymentByExternalIdRequest(external_id=payment.external_id))
    assert stored.status == PaymentStatus.PAID and stored.paid_at is not None
    assert (await run(GetUserAccessRequest(tg_id=trainer.tg_id))).trainer_subscription_active
    assert [e.event.value for e in notifications.of("notify_subscription")] == ["paid"]
    assert len(notifications.of("notify_admins")) == 1


async def test_manual_payment_goes_to_admins_then_approved(run, notifications) -> None:
    trainer, plan = await _trainer_and_plan(run)
    created = await run(
        CreateSubscriptionPaymentRequest(trainer_id=trainer.id, price_plan_id=plan.id, method=PaymentMethod.MANUAL)
    )
    assert created.payment.status == PaymentStatus.WAITING_CONFIRMATION
    assert "@boss" in created.instructions.text and created.instructions.url is None
    [request] = notifications.of("notify_manual_payment_request")
    assert request.external_id == created.payment.external_id

    await run(ConfirmPaymentRequest(external_id=created.payment.external_id))

    from src.application.use_cases.subscription.get_active import GetActiveSubscriptionRequest

    subscription = await run(GetActiveSubscriptionRequest(trainer_id=trainer.id))
    assert subscription.source == SubscriptionSource.CASH  # ручная → «через администратора»


async def test_rejected_payment_cannot_be_confirmed(run, notifications) -> None:
    trainer, plan = await _trainer_and_plan(run)
    created = await run(
        CreateSubscriptionPaymentRequest(trainer_id=trainer.id, price_plan_id=plan.id, method=PaymentMethod.MANUAL)
    )
    await run(RejectPaymentRequest(external_id=created.payment.external_id, notify_trainer=True))
    assert any("не подтвердил оплату" in text for _, text in notifications.of("send"))

    with pytest.raises(PaymentStatusTransitionException):
        await run(ConfirmPaymentRequest(external_id=created.payment.external_id))


async def test_paid_payment_cannot_be_rejected(run) -> None:
    trainer, plan = await _trainer_and_plan(run)
    created = await run(
        CreateSubscriptionPaymentRequest(trainer_id=trainer.id, price_plan_id=plan.id, method=PaymentMethod.YOOKASSA)
    )
    await run(ConfirmPaymentRequest(external_id=created.payment.external_id))
    with pytest.raises(PaymentStatusTransitionException):
        await run(RejectPaymentRequest(external_id=created.payment.external_id))


async def test_test_provider_confirms_immediately(run) -> None:
    trainer, plan = await _trainer_and_plan(run)
    created = await run(
        CreateSubscriptionPaymentRequest(trainer_id=trainer.id, price_plan_id=plan.id, method=PaymentMethod.TEST)
    )
    assert created.payment.status == PaymentStatus.PAID
    assert (await run(GetUserAccessRequest(tg_id=trainer.tg_id))).trainer_subscription_active


async def test_disabled_method_rejected(run) -> None:
    trainer, plan = await _trainer_and_plan(run)
    with pytest.raises(PaymentProviderNotFoundException):
        await run(
            CreateSubscriptionPaymentRequest(
                trainer_id=trainer.id, price_plan_id=plan.id, method=PaymentMethod.TELEGRAM_STARS
            )
        )
