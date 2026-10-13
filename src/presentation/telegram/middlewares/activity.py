import logging
from collections.abc import Awaitable, Callable
from datetime import date
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from dishka import AsyncContainer
from dishka.integrations.aiogram import CONTAINER_NAME

from src.application.mediator import Mediator
from src.application.use_cases.bot_user.track_activity import TrackUserActivityRequest
from src.domain.utils import get_project_today

logger = logging.getLogger(__name__)

Handler = Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]]


class ActivityTrackingMiddleware(BaseMiddleware):
    """
    Outer-middleware (после dishka): отмечает, что пользователь был в боте
    сегодня — для аналитики админа (новые, DAU/WAU/MAU). В БД пишем не чаще
    раза в день на пользователя: последний отмеченный день держим в памяти
    процесса (после рестарта — максимум одна лишняя запись, upsert идемпотентен).
    """

    def __init__(self) -> None:
        self._seen: dict[int, date] = {}

    def reset(self) -> None:
        self._seen.clear()

    async def __call__(self, handler: Handler, event: TelegramObject, data: dict[str, Any]) -> Any:
        user: User | None = data.get("event_from_user")
        chat = data.get("event_chat")
        # кнопки в рабочих группах тренера — не активность пользователя в боте
        if user is not None and not user.is_bot and (chat is None or chat.type == "private"):
            await self._track(user, data)
        return await handler(event, data)

    async def _track(self, user: User, data: dict[str, Any]) -> None:
        today = get_project_today()
        if self._seen.get(user.id) == today:
            return
        try:
            container: AsyncContainer = data[CONTAINER_NAME]
            mediator = await container.get(Mediator)
            await mediator.handle(
                TrackUserActivityRequest(
                    tg_id=user.id, username=user.username, first_name=user.first_name
                )
            )
        except Exception:
            # аналитика не должна ломать ответ пользователю
            logger.exception("[ActivityTracking] tg_id=%s", user.id)
            return
        if len(self._seen) > 100_000:
            self._seen.clear()
        self._seen[user.id] = today
