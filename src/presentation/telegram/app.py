import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault
from dishka import make_async_container
from dishka.integrations.aiogram import AiogramProvider, setup_dishka
from taskiq_redis import RedisStreamBroker

from src.infrastructure.database.seed import (
    seed_faq_items,
    seed_subscription_price_plans,
)
from src.infrastructure.taskiq.tasks import register_taskiq_tasks
from src.utils.logging import setup_logging
from src.application.services.payment_provider_registry import PaymentProviderRegistry
from src.presentation.telegram.dialog_ids import patch_dialog_intent_ids
from src.presentation.telegram.middlewares.setup import setup_middlewares
from src.core.dependencies.providers import make_base_providers


logger = logging.getLogger(__name__)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Главное меню"),
        BotCommand(command="/trainer", description="Кабинет тренера"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


async def create_app():
    setup_logging("bot")
    patch_dialog_intent_ids()

    container = make_async_container(
        *make_base_providers(),
        AiogramProvider(),
    )
    broker: RedisStreamBroker = await container.get(RedisStreamBroker)

    register_taskiq_tasks(broker, container=container)
    await broker.startup()

    await seed_subscription_price_plans(container)
    await container.get(PaymentProviderRegistry)  # лог включённых способов оплаты
    await seed_faq_items(container)

    bot: Bot = await container.get(Bot)
    dp: Dispatcher = await container.get(Dispatcher)

    await set_commands(bot)

    setup_dishka(container=container, router=dp)
    setup_middlewares(dp)

    await bot.delete_webhook(drop_pending_updates=True)

    try:
        logger.info("🤖 Бот запущен…")
        await dp.start_polling(bot)
    finally:
        await broker.shutdown()
        await bot.session.close()
        logger.info("🧹 Бот остановлен.")


if __name__ == "__main__":
    asyncio.run(create_app())