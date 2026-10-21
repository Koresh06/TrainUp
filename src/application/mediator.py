import logging
import time
from typing import Any, Dict, Type, TypeVar

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.exception.base import DomainError

logger = logging.getLogger(__name__)

Req = TypeVar("Req", bound=UseCaseRequest)
Res = TypeVar("Res")

# запрос дольше — WARNING: подозрение на тяжёлый запрос к БД / внешний API
SLOW_REQUEST_SECONDS = 1.0
# repr запроса в логе обрезаем: в анкетах бывают длинные тексты
REQUEST_REPR_LIMIT = 300


def _short(request: UseCaseRequest) -> str:
    text = repr(request)
    return text if len(text) <= REQUEST_REPR_LIMIT else text[:REQUEST_REPR_LIMIT] + "…"


class Mediator:
    def __init__(self) -> None:
        self._handlers: Dict[Type[UseCaseRequest], UseCase[Any, Any]] = {}

    def register(self, request_type: Type[Req], handler: UseCase[Req, Res]) -> None:
        self._handlers[request_type] = handler

    async def handle(self, request: Req) -> Res:
        """
        Единая точка вызова use case'ов — здесь же их логирование: DEBUG на каждый
        вызов, WARNING на медленные и бизнес-ошибки, ERROR с traceback на падения.
        Так в логе видно, какой use case и с какими параметрами сломался, даже
        если сам use case ничего не пишет.
        """
        for cls in type(request).mro():
            handler = self._handlers.get(cls)
            if handler is not None:
                break
        else:
            raise ValueError(f"No handler registered for {type(request)}")

        name = type(request).__name__
        started = time.monotonic()
        try:
            result = await handler(request)  # type: ignore[return-value]
        except DomainError as error:
            # ожидаемые отказы (слот занят, запись уже отменена) — не авария
            logger.info("[Mediator] %s rejected: %s | %s", name, error.message, _short(request))
            raise
        except Exception:
            logger.exception(
                "[Mediator] %s failed in %.2fs | %s",
                name, time.monotonic() - started, _short(request),
            )
            raise

        elapsed = time.monotonic() - started
        if elapsed > SLOW_REQUEST_SECONDS:
            logger.warning("[Mediator] %s slow: %.2fs | %s", name, elapsed, _short(request))
        else:
            logger.debug("[Mediator] %s ok in %.3fs", name, elapsed)
        return result
