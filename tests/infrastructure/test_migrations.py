"""Миграции против реального Postgres: применяются с нуля, откатываются
и не расходятся с ORM-моделями (то, что в проде показал бы `alembic check`)."""

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from src.infrastructure.database.models import BaseModel


async def _diff(url: str):
    engine = create_async_engine(url, poolclass=NullPool)
    async with engine.connect() as conn:
        diff = await conn.run_sync(
            lambda sync_conn: compare_metadata(
                MigrationContext.configure(sync_conn), BaseModel.metadata
            )
        )
        tables = await conn.run_sync(lambda c: set(inspect(c).get_table_names()))
    await engine.dispose()
    return diff, tables


async def test_upgrade_head_creates_every_model_table(migrated_db: str) -> None:
    _, tables = await _diff(migrated_db)
    assert set(BaseModel.metadata.tables) <= tables


async def test_migrated_schema_matches_models(migrated_db: str) -> None:
    diff, _ = await _diff(migrated_db)
    assert diff == [], f"Схема после миграций расходится с моделями: {diff}"


async def test_bot_users_backfilled_from_registered_users(db: str) -> None:
    # аудитория до запуска аналитики не должна пропасть из «Всего пользователей»
    import asyncio

    from alembic import command
    from alembic.config import Config
    from sqlalchemy import text

    from src.core.config.database import PostgresSettings

    original_url = PostgresSettings.url
    PostgresSettings.url = property(lambda self: db)  # type: ignore[method-assign,assignment]
    engine = create_async_engine(db, poolclass=NullPool)
    try:
        # env.py миграций сам делает asyncio.run — из running loop только в потоке
        await asyncio.to_thread(command.downgrade, Config("alembic.ini"), "af71f1ec3e1b")
        async with engine.begin() as conn:
            await conn.execute(text(
                "INSERT INTO trainers (tg_id, name, bio, notification_chat_id, is_active, social_links) "
                "VALUES (1, 'Тренер', '', -1, true, '{}')"
            ))
            await conn.execute(text(
                "INSERT INTO clients (tg_id, trainer_id, first_name, username, phone, age, "
                "sport_experience, is_active) VALUES (2, 1, 'Анна', 'anna', '+375', 30, 'NONE', true)"
            ))
        await asyncio.to_thread(command.upgrade, Config("alembic.ini"), "head")
        async with engine.connect() as conn:
            rows = (await conn.execute(
                text("SELECT tg_id, first_name, username FROM bot_users ORDER BY tg_id")
            )).all()
    finally:
        PostgresSettings.url = original_url  # type: ignore[method-assign]
        await engine.dispose()

    assert [tuple(r) for r in rows] == [(1, "Тренер", None), (2, "Анна", "anna")]
