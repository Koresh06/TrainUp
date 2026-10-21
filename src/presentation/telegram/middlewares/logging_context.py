import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from src.utils.logging import log_context

logger = logging.getLogger(__name__)

Handler = Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]]

# дольше — пишем WARNING: пользователь ждал ответа бота
SLOW_UPDATE_SECONDS = 3.0


def describe_update(update: Update) -> tuple[int | None, str]:
    """Кто и что сделал — без текста сообщений (там бывают телефоны и анкеты)."""
    if update.callback_query is not None:
        query = update.callback_query
        # callback aiogram_dialog: «<intent>\\x1d<виджет>:<значение>»
        data = (query.data or "").replace("\x1d", "/")
        return query.from_user.id, f"cb={data}"
    if update.message is not None:
        message = update.message
        user_id = message.from_user.id if message.from_user else None
        text = message.text or ""
        if text.startswith("/"):
            return user_id, f"cmd={text.split()[0]}"
        if text:
            return user_id, f"text[{len(text)}]"
        return user_id, f"msg={message.content_type}"
    if update.my_chat_member is not None:
        member = update.my_chat_member
        return member.from_user.id, f"chat_member={member.new_chat_member.status}"
    if update.pre_checkout_query is not None:
        return update.pre_checkout_query.from_user.id, "pre_checkout"
    return None, f"update={update.event_type}"


class LoggingContextMiddleware(BaseMiddleware):
    """
    Самый первый middleware апдейта: кладёт «u=<id> <действие>» в контекст
    логов — его видно в каждой строке, записанной во время обработки
    (use case'ы, репозитории, уведомления), и пишет одну строку на апдейт
    с длительностью.
    """

    async def __call__(self, handler: Handler, event: TelegramObject, data: dict[str, Any]) -> Any:
        if not isinstance(event, Update):
            return await handler(event, data)

        user_id, action = describe_update(event)
        token = log_context.set(f"u={user_id or '-'} {action}")
        started = time.monotonic()
        try:
            return await handler(event, data)
        finally:
            elapsed = time.monotonic() - started
            log = logger.warning if elapsed > SLOW_UPDATE_SECONDS else logger.info
            log("[Update] id=%s handled in %.2fs", event.update_id, elapsed)
            log_context.reset(token)
