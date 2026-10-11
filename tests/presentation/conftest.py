"""Прокликивание диалогов бота без Telegram (aiogram_dialog.test_tools) на
реальной БД. Диспетчер собирается один раз на сессию — роутеры aiogram нельзя
подключить к двум диспетчерам; DI-контейнер подменяется на каждый тест."""

import re
from dataclasses import replace
from types import SimpleNamespace

import pytest
from aiogram import BaseMiddleware, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup
from aiogram_dialog import setup_dialogs
from aiogram_dialog.test_tools import BotClient, MockMessageManager
from aiogram_dialog.test_tools import bot_client as test_bot_client
from aiogram_dialog.test_tools.keyboard import InlineButtonTextLocator
from dishka.integrations.aiogram import CONTAINER_NAME

from src.presentation.telegram.dialog_ids import patch_dialog_intent_ids
from src.presentation.telegram.features import get_all_dialogs, get_all_routers
from src.presentation.telegram.middlewares.setup import setup_middlewares

BOT_CALLS: list = []


async def _fake_bot_call(self, method, request_timeout=None):
    # прямые вызовы API из хендлеров (message.answer, answer_document, copy_message…)
    BOT_CALLS.append(method)
    return True


class ReplyKeyboardSafeMessageManager(MockMessageManager):
    # MockMessageManager умеет только inline-клавиатуры; окна с RequestContact /
    # RequestChat отдают reply-клавиатуру — для теста она не важна
    async def show_message(self, bot, new_message, old_message):
        if isinstance(new_message.reply_markup, ReplyKeyboardMarkup):
            new_message = replace(new_message, reply_markup=None)
        return await super().show_message(bot, new_message, old_message)


class SwitchableContainerMiddleware(BaseMiddleware):
    """Аналог dishka ContainerMiddleware с подменяемым контейнером."""

    container = None

    async def __call__(self, handler, event, data):
        async with self.container() as request_container:
            data[CONTAINER_NAME] = request_container
            return await handler(event, data)


@pytest.fixture(scope="session")
def ui_env():
    test_bot_client.FakeBot.__call__ = _fake_bot_call
    patch_dialog_intent_ids()  # как в app.py: иначе id диалогов совпадают в одну секунду

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_routers(*get_all_routers())
    dp.include_routers(*get_all_dialogs())
    message_manager = ReplyKeyboardSafeMessageManager()
    setup_dialogs(dp, message_manager=message_manager)

    switch = SwitchableContainerMiddleware()
    for observer in dp.observers.values():
        observer.outer_middleware(switch)
    setup_middlewares(dp)
    return SimpleNamespace(dp=dp, mm=message_manager, switch=switch)


class UI:
    def __init__(self, env) -> None:
        self.dp = env.dp
        self.mm = env.mm
        self._clients: dict[int, BotClient] = {}

    def client(self, user_id: int) -> BotClient:
        if user_id not in self._clients:
            self._clients[user_id] = BotClient(self.dp, user_id=user_id, chat_id=user_id)
        return self._clients[user_id]

    @property
    def last(self):
        return self.mm.last_message() if self.mm.sent_messages else None

    @property
    def text(self) -> str:
        return self.last.text if self.last else ""

    @property
    def buttons(self) -> list[str]:
        markup = self.last.reply_markup if self.last else None
        if markup is None:
            return []
        return [b.text for row in markup.inline_keyboard for b in row]

    async def send(self, user_id: int, text: str) -> str:
        self.mm.reset_history()
        await self.client(user_id).send(text)
        return self.text

    async def click(self, user_id: int, button_text: str) -> str:
        message = self.last
        self.mm.reset_history()
        try:
            await self.client(user_id).click(
                message, InlineButtonTextLocator(re.escape(button_text))
            )
        except Exception as error:
            raise AssertionError(
                f"click {button_text!r} failed on message:\n{message.text if message else None}\n"
                f"buttons: {[b.text for row in message.reply_markup.inline_keyboard for b in row] if message and message.reply_markup else []}\n"
                f"callback: {[b.callback_data for row in message.reply_markup.inline_keyboard for b in row] if message and message.reply_markup else []}"
            ) from error
        return self.text

    def sent_texts(self) -> list[str]:
        return [getattr(m, "text", "") or "" for m in BOT_CALLS]


@pytest.fixture
def ui(ui_env, container) -> UI:
    ui_env.switch.container = container
    ui_env.mm.reset_history()
    ui_env.dp.storage.storage.clear()  # MemoryStorage: стек диалогов между тестами не нужен
    BOT_CALLS.clear()
    return UI(ui_env)
