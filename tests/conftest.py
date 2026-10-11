"""Общие настройки тестов.

Настройки приложения читаются из .env разработчика (там могут быть включены
тестовые режимы напоминаний и т.п.). Переменные окружения приоритетнее .env,
поэтому фиксируем боевые бизнес-параметры ДО первого импорта настроек.
"""

import os

os.environ.update(
    {
        "APP_CONFIG__BUSINESS__TIMEZONE": "Europe/Moscow",
        "APP_CONFIG__BUSINESS__REMINDER_TEST_MODE": "False",
        "APP_CONFIG__BUSINESS__RECURRING_BOOKINGS_TEST_MODE": "False",
        "APP_CONFIG__BUSINESS__REMINDER_HOURS_BEFORE_TRAINING": "2",
        "APP_CONFIG__BUSINESS__DEFAULT_MAX_ACTIVE_BOOKINGS": "1",
        "APP_CONFIG__BUSINESS__PLAN_NEXT_TRAINING_REMINDER_DAYS": "3",
        "APP_CONFIG__BUSINESS__SUBSCRIPTION_WARNING_HOURS": "[48, 3]",
        "APP_CONFIG__TELEGRAM__ADMIN_IDS": "[777000]",
        "APP_CONFIG__TELEGRAM__BOT_TOKEN": "123456:TEST-TOKEN-not-real",
        # способы оплаты в тестах: ручная + тестовая; ЮKassa/Stars — фейками в тестах
        "APP_CONFIG__PAYMENT__TEST_MODE": "True",
        "APP_CONFIG__PAYMENT__MANUAL__ENABLED": "True",
        "APP_CONFIG__PAYMENT__MANUAL__ADMIN_CONTACT": "@trainup_admin",
        "APP_CONFIG__PAYMENT__YOOKASSA__ENABLED": "False",
        "APP_CONFIG__PAYMENT__TELEGRAM_STARS__ENABLED": "False",
    }
)

from src.core.config import settings  # noqa: E402

assert settings.business.reminder_test_mode is False
assert settings.telegram.admin_ids == [777000]


# --- Реальный PostgreSQL для infrastructure/integration/presentation тестов ---
# Поднимается встроенным pgserver (бинарники из wheel, без docker) только если
# тест запросил эти фикстуры; схема — настоящими alembic-миграциями, так что
# тесты заодно проверяют, что миграции применяются с нуля.

import tempfile  # noqa: E402
from collections.abc import AsyncIterator, Iterator  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool  # noqa: E402

TEST_DB = "trainup_test"


@pytest.fixture(scope="session")
def pg_url() -> Iterator[str]:
    pgserver = pytest.importorskip("pgserver")
    data_dir = tempfile.mkdtemp(prefix="trainup_pg_")
    server = pgserver.get_server(data_dir, cleanup_mode="delete")
    server.psql(f"CREATE DATABASE {TEST_DB};")
    socket_dir = server.get_uri().split("host=")[-1]
    yield f"postgresql+asyncpg://postgres@/{TEST_DB}?host={socket_dir}"
    server.cleanup()


@pytest.fixture(scope="session")
def migrated_db(pg_url: str) -> str:
    from alembic import command
    from alembic.config import Config

    from src.core.config.database import PostgresSettings

    original_url = PostgresSettings.url
    PostgresSettings.url = property(lambda self: pg_url)  # type: ignore[method-assign,assignment]
    try:
        command.upgrade(Config("alembic.ini"), "head")
    finally:
        PostgresSettings.url = original_url  # type: ignore[method-assign]
    return pg_url


async def _truncate_all(url: str) -> None:
    from src.infrastructure.database.models import BaseModel

    tables = ", ".join(BaseModel.metadata.tables)
    engine = create_async_engine(url, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    await engine.dispose()


@pytest.fixture
async def db(migrated_db: str) -> AsyncIterator[str]:
    """Чистая БД на тест: таблицы очищаются после каждого теста."""
    yield migrated_db
    await _truncate_all(migrated_db)


@pytest.fixture
async def session(db: str) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(db, poolclass=NullPool)
    async with AsyncSession(engine, expire_on_commit=False) as s:
        yield s
    await engine.dispose()


@pytest.fixture
async def app_session_maker(db: str, monkeypatch) -> AsyncIterator[async_sessionmaker]:
    """Подменяет фабрику сессий DI-контейнера на тестовую БД."""
    engine = create_async_engine(db, poolclass=NullPool)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr("src.core.dependencies.providers.base.async_session_maker", maker)
    yield maker
    await engine.dispose()


# --- DI-контейнер приложения: внешние системы (Telegram, taskiq, Redis) — фейки ---

from dishka import Provider, Scope, make_async_container, provide  # noqa: E402
from redis.asyncio import Redis  # noqa: E402

from src.application.interfaces.notification_service import NotificationService  # noqa: E402
from src.application.interfaces.task_queue import TaskQueue  # noqa: E402
from src.application.mediator import Mediator  # noqa: E402
from src.core.dependencies.providers import make_base_providers  # noqa: E402
from tests.fakes.common import FakeTaskQueue, RecordingNotifications  # noqa: E402


class FakeExternalsProvider(Provider):
    def __init__(self, notifications: RecordingNotifications, queue: FakeTaskQueue) -> None:
        super().__init__()
        self._notifications = notifications
        self._queue = queue

    @provide(scope=Scope.REQUEST, override=True)
    def notifications(self) -> NotificationService:
        return self._notifications

    @provide(scope=Scope.REQUEST, override=True)
    def queue(self) -> TaskQueue:
        return self._queue

    @provide(scope=Scope.APP, override=True)
    def redis(self) -> Redis:
        import fakeredis

        return fakeredis.FakeAsyncRedis()


@pytest.fixture
def notifications() -> RecordingNotifications:
    return RecordingNotifications()


@pytest.fixture
def task_queue() -> FakeTaskQueue:
    return FakeTaskQueue()


@pytest.fixture
async def container(app_session_maker, notifications, task_queue):
    c = make_async_container(
        *make_base_providers(), FakeExternalsProvider(notifications, task_queue)
    )
    yield c
    await c.close()


@pytest.fixture
def run(container):
    """Выполняет запрос через Mediator в отдельном request-scope (как хендлер бота)."""

    async def _run(request):
        async with container() as request_container:
            mediator = await request_container.get(Mediator)
            return await mediator.handle(request)

    return _run
