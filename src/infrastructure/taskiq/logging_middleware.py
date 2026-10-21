import logging
import time
from contextvars import Token
from typing import Any

from taskiq import TaskiqMessage, TaskiqMiddleware, TaskiqResult

from src.utils.logging import log_context

logger = logging.getLogger(__name__)


class TaskLoggingMiddleware(TaskiqMiddleware):
    """
    Лог каждой фоновой задачи: старт, длительность, ошибка с traceback.
    Контекст «task=<имя> id=<id>» попадает во все строки, записанные
    внутри задачи (use case'ы, уведомления).
    """

    def __init__(self) -> None:
        super().__init__()
        self._started: dict[str, tuple[float, Token]] = {}

    async def pre_execute(self, message: TaskiqMessage) -> TaskiqMessage:
        token = log_context.set(f"task={message.task_name} id={message.task_id[:8]}")
        self._started[message.task_id] = (time.monotonic(), token)
        logger.info("[Task] start args=%s", message.args)
        return message

    async def post_execute(self, message: TaskiqMessage, result: TaskiqResult[Any]) -> None:
        started, token = self._started.pop(message.task_id, (time.monotonic(), None))
        elapsed = time.monotonic() - started
        if result.is_err:
            logger.error("[Task] failed in %.2fs: %r", elapsed, result.error)
        else:
            logger.info("[Task] done in %.2fs", elapsed)
        if token is not None:
            log_context.reset(token)

    async def on_error(
        self, message: TaskiqMessage, result: TaskiqResult[Any], exception: BaseException
    ) -> None:
        logger.error("[Task] error in %s", message.task_name, exc_info=exception)
