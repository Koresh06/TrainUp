from contextlib import asynccontextmanager

from dishka import make_async_container
from dishka.integrations.fastapi import FastapiProvider, setup_dishka
from fastapi import FastAPI
from taskiq_redis import RedisStreamBroker

from src.application.services.payment_provider_registry import PaymentProviderRegistry
from src.core.dependencies.providers import make_base_providers
from src.infrastructure.taskiq.tasks import register_taskiq_tasks
from src.presentation.web.routers.result import router as result_router
from src.presentation.web.routers.yookassa import router as yookassa_router
from src.utils.logging import setup_logging

container = make_async_container(*make_base_providers(), FastapiProvider())


@asynccontextmanager
async def lifespan(app: FastAPI):
    # webhook только ставит задачи в очередь — подтверждает платёж воркер
    await container.get(PaymentProviderRegistry)  # лог включённых способов оплаты
    broker: RedisStreamBroker = await container.get(RedisStreamBroker)
    register_taskiq_tasks(broker, container=container)
    await broker.startup()
    yield
    await broker.shutdown()
    await container.close()


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    app.include_router(yookassa_router)
    app.include_router(result_router)
    setup_dishka(container=container, app=app)
    return app


# запуск: uvicorn src.presentation.web.app:create_app --host 0.0.0.0 --port 8080 --factory
