from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.application.interfaces.payment_provider import InvoiceRequestDTO
from src.application.services.payment_provider_registry import PaymentProviderRegistry
from src.core.config.payment import TelegramStarsSettings, YooKassaSettings
from src.domain.entities.payment import Payment
from src.domain.enums.payment import PaymentMethod, PaymentPurpose
from src.domain.exception.payment import (
    PaymentAmountInvalidException,
    PaymentProviderNotFoundException,
)
from src.infrastructure.payment.providers.telegram_stars import TelegramStarsProvider
from src.infrastructure.payment.providers.yookassa import YooKassaProvider
from src.presentation.web.routers.yookassa import process_yookassa_webhook
from tests.fakes.common import FakeTaskQueue

REQUEST = InvoiceRequestDTO(
    external_id="ext1", amount=Decimal("10"), description="Подписка TrainUp: 1 месяц", trainer_tg_id=5
)


class FakeStarsBot:
    def __init__(self) -> None:
        self.invoices: list[dict] = []

    async def create_invoice_link(self, **kwargs) -> str:
        self.invoices.append(kwargs)
        return "https://t.me/$invoice"


async def test_stars_converts_usd_to_stars_rounding_up() -> None:
    bot = FakeStarsBot()
    provider = TelegramStarsProvider(bot=bot, settings=TelegramStarsSettings(usd_per_star=Decimal("0.03")))
    meta = await provider.create_invoice(REQUEST)

    assert meta["stars_amount"] == 334  # 10 / 0.03 = 333.3 → вверх
    [invoice] = bot.invoices
    assert invoice["currency"] == "XTR" and invoice["payload"] == "ext1"
    assert invoice["prices"][0].amount == 334


async def test_stars_rejects_zero_amount() -> None:
    provider = TelegramStarsProvider(bot=FakeStarsBot(), settings=TelegramStarsSettings())
    with pytest.raises(PaymentAmountInvalidException):
        await provider.create_invoice(
            InvoiceRequestDTO(external_id="x", amount=Decimal("0"), description="d", trainer_tg_id=1)
        )


def test_yookassa_converts_usd_to_rub() -> None:
    provider = YooKassaProvider(YooKassaSettings(usd_to_rub_rate=Decimal("92.5")))
    assert provider.to_rub(Decimal("29.99")) == Decimal("2774.08")
    payment = Payment(
        external_id="e", trainer_id=1, method=PaymentMethod.YOOKASSA, amount=Decimal("10"),
        purpose=PaymentPurpose.SUBSCRIPTION,
        meta={"amount_rub": "925.00", "usd_to_rub_rate": "92.5", "confirmation_url": "https://y"},
    )
    instructions = provider.get_instructions(payment)
    assert "925.00 ₽" in instructions.text and instructions.url == "https://y"


def test_registry_unknown_method() -> None:
    with pytest.raises(PaymentProviderNotFoundException):
        PaymentProviderRegistry().get(PaymentMethod.YOOKASSA)


class FakeYooKassa(YooKassaProvider):
    """Без SDK: verify_payment отдаёт заранее заданный «ответ API»."""

    def __init__(self, verified) -> None:
        self._verified = verified

    async def verify_payment(self, yookassa_payment_id: str):
        return self._verified


def _registry(provider) -> PaymentProviderRegistry:
    registry = PaymentProviderRegistry()
    registry.register(provider)
    return registry


@pytest.mark.parametrize(
    "status, paid, expected_task",
    [("succeeded", True, "confirm_payment"), ("canceled", False, "reject_payment"), ("pending", False, None)],
)
async def test_webhook_trusts_only_verified_status(status, paid, expected_task) -> None:
    queue = FakeTaskQueue()
    verified = SimpleNamespace(status=status, paid=paid, metadata={"external_id": "ext1"})
    # тело webhook'а «врёт», что платёж успешен — решает только ответ API
    payload = {"event": "payment.succeeded", "object": {"id": "yk-1", "status": "succeeded"}}

    await process_yookassa_webhook(payload, task_queue=queue, provider_registry=_registry(FakeYooKassa(verified)))

    assert [t for t, _ in queue.enqueued] == ([expected_task] if expected_task else [])


async def test_webhook_asks_retry_when_api_unavailable() -> None:
    with pytest.raises(HTTPException) as error:
        await process_yookassa_webhook(
            {"object": {"id": "yk-1"}}, task_queue=FakeTaskQueue(),
            provider_registry=_registry(FakeYooKassa(None)),
        )
    assert error.value.status_code == 502


async def test_payment_repo_roundtrip(session) -> None:
    from src.infrastructure.repositories.payment.sqlalchemy import SQLAlchemyPaymentRepo
    from tests.factories import make_trainer

    trainer = await make_trainer(session)
    repo = SQLAlchemyPaymentRepo(session)
    saved = await repo.save(
        Payment(
            external_id="abc", trainer_id=trainer.id, method=PaymentMethod.TELEGRAM_STARS,
            amount=Decimal("12.50"), purpose=PaymentPurpose.SUBSCRIPTION, purpose_id=1,
            meta={"stars_amount": 625},
        )
    )
    await session.commit()
    saved.mark_paid(datetime.now(timezone.utc))
    await repo.save(saved)
    await session.commit()

    session.expunge_all()
    loaded = await repo.get_by_external_id_for_update("abc")
    assert loaded.meta == {"stars_amount": 625} and loaded.paid_at is not None
    assert loaded.amount == Decimal("12.50")
