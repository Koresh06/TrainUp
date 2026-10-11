"""HTTP-слой webhook-сервиса: роуты подключены, DI работает, страница возврата."""

from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.application.services.payment_provider_registry import PaymentProviderRegistry
from src.application.interfaces.task_queue import TaskQueue
from src.infrastructure.payment.providers.yookassa import YooKassaProvider
from src.presentation.web.routers.result import router as result_router
from src.presentation.web.routers.yookassa import router as yookassa_router
from tests.fakes.common import FakeTaskQueue


def _app(registry: PaymentProviderRegistry, queue: FakeTaskQueue):
    from dishka import Provider, Scope, make_async_container, provide
    from dishka.integrations.fastapi import FastapiProvider, setup_dishka
    from fastapi import FastAPI

    from src.application.mediator import Mediator

    class WebFakes(Provider):
        @provide(scope=Scope.APP)
        def registry(self) -> PaymentProviderRegistry:
            return registry

        @provide(scope=Scope.APP)
        def queue(self) -> TaskQueue:
            return queue

        @provide(scope=Scope.REQUEST)
        def mediator(self) -> Mediator:
            return Mediator()  # страница возврата без external_id в БД не ходит

    app = FastAPI()
    app.include_router(yookassa_router)
    app.include_router(result_router)
    setup_dishka(make_async_container(WebFakes(), FastapiProvider()), app)
    return app


class VerifiedYooKassa(YooKassaProvider):
    def __init__(self) -> None:
        pass

    async def verify_payment(self, yookassa_payment_id: str):
        return SimpleNamespace(status="succeeded", paid=True, metadata={"external_id": "ext-42"})


def test_webhook_route_enqueues_confirmation() -> None:
    registry = PaymentProviderRegistry()
    registry.register(VerifiedYooKassa())
    queue = FakeTaskQueue()
    with TestClient(_app(registry, queue)) as client:
        response = client.post("/webhook/yookassa", json={"event": "payment.succeeded", "object": {"id": "yk"}})
    assert response.status_code == 200
    assert queue.enqueued == [("confirm_payment", ("ext-42",))]


def test_webhook_404_when_yookassa_disabled() -> None:
    with TestClient(_app(PaymentProviderRegistry(), FakeTaskQueue())) as client:
        response = client.post("/webhook/yookassa", json={"object": {"id": "yk"}})
    assert response.status_code == 404


def test_return_page_without_payment() -> None:
    with TestClient(_app(PaymentProviderRegistry(), FakeTaskQueue())) as client:
        response = client.get("/payment/return")
    assert response.status_code == 200
    assert "Оплата не прошла" in response.text and "t.me/" in response.text
