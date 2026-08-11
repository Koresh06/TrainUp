import orjson

from dishka import Provider, provide, Scope
from redis.asyncio.client import Redis
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram_dialog import setup_dialogs

from src.core.config import settings
from src.presentation.telegram.features import get_all_dialogs, get_all_routers


class TelegramProvider(Provider):
    scope = Scope.APP

    @provide
    def bot(self) -> Bot:
        proxy = settings.telegram.bot_proxy
        session = AiohttpSession(proxy=proxy) if proxy else AiohttpSession()
        return Bot(
            token=settings.telegram.bot_token,
            session=session,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )

    @provide
    def fsm_storage(self, redis: Redis) -> RedisStorage:
        return RedisStorage(
            redis=redis,
            key_builder=DefaultKeyBuilder(with_destiny=True),
            json_loads=orjson.loads,
        )

    @provide
    def dispatcher(self, bot: Bot, fsm_storage: RedisStorage) -> Dispatcher:
        dp = Dispatcher(bot=bot, storage=fsm_storage)

        dp.include_routers(*get_all_routers())
        dp.include_routers(*get_all_dialogs())

        setup_dialogs(dp) 

        return dp
