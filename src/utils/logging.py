"""Логирование всех процессов (бот, воркер, планировщик, webhook).

Каждая строка: время, уровень, сервис, контекст апдейта/задачи, логгер:строка,
сообщение. Контекст (кто нажал, какой callback, какая задача) кладут
middleware бота и taskiq — по нему ошибка в логе сразу связывается с
пользователем и действием.

Куда пишем:
- консоль (docker logs), цветная в терминале;
- logs/<service>.log — всё от INFO, ротация 10 МБ × 5;
- logs/errors.log — WARNING и выше всех сервисов, ротация 10 МБ × 5.
"""

import logging
import sys
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.core.config import settings

# «u=123 cb=booking:confirm:5» / «task=send_trainer_digests» — ставят middleware
log_context: ContextVar[str] = ContextVar("log_context", default="-")

FORMAT = (
    "%(asctime)s | %(levelname)-7s | %(service)s | %(context)s | "
    "%(name)s:%(lineno)d | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 10 * 1024 * 1024
BACKUP_COUNT = 5

# библиотеки, которые на INFO пишут каждую мелочь
NOISY_LOGGERS = {
    "aiogram.event": logging.WARNING,  # «Update id=… is handled» на каждый апдейт
    "aiogram.dispatcher": logging.INFO,
    "aiogram_dialog": logging.WARNING,
    "sqlalchemy.engine": logging.WARNING,
    "httpx": logging.WARNING,
    "httpcore": logging.WARNING,
    "matplotlib": logging.WARNING,
    "PIL": logging.WARNING,
    "taskiq.receiver.receiver": logging.WARNING,
    "uvicorn.access": logging.WARNING,
}

_COLORS = {
    logging.DEBUG: "\033[37m",
    logging.INFO: "\033[36m",
    logging.WARNING: "\033[33m",
    logging.ERROR: "\033[31m",
    logging.CRITICAL: "\033[1;31m",
}
_RESET = "\033[0m"


class _ContextFilter(logging.Filter):
    def __init__(self, service: str) -> None:
        super().__init__()
        self._service = service

    def filter(self, record: logging.LogRecord) -> bool:
        record.service = self._service
        record.context = log_context.get()
        return True


class _ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        color = _COLORS.get(record.levelno)
        return f"{color}{text}{_RESET}" if color else text


def setup_logging(service: str = "app") -> None:
    """Вызывается один раз при старте процесса; повторный вызов не дублирует хендлеры."""
    level = logging.getLevelName(settings.app.log_level.upper())
    if not isinstance(level, int):
        level = logging.INFO

    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
    root.setLevel(level)
    context_filter = _ContextFilter(service)

    console = logging.StreamHandler(sys.stdout)
    formatter_cls = _ColorFormatter if sys.stdout.isatty() else logging.Formatter
    console.setFormatter(formatter_cls(FORMAT, DATE_FORMAT))
    console.addFilter(context_filter)
    root.addHandler(console)

    if settings.app.log_dir:
        log_dir = Path(settings.app.log_dir)
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            for path, file_level in (
                (log_dir / f"{service}.log", level),
                (log_dir / "errors.log", logging.WARNING),
            ):
                handler = RotatingFileHandler(
                    path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
                )
                handler.setLevel(file_level)
                handler.setFormatter(logging.Formatter(FORMAT, DATE_FORMAT))
                handler.addFilter(context_filter)
                root.addHandler(handler)
        except OSError as error:
            # нет прав на каталог — пишем хотя бы в консоль, но не падаем
            root.warning("[Logging] file logs disabled: %s", error)

    for name, noisy_level in NOISY_LOGGERS.items():
        logging.getLogger(name).setLevel(max(noisy_level, level))

    logging.getLogger(__name__).info(
        "[Logging] service=%s level=%s dir=%s",
        service, logging.getLevelName(level), settings.app.log_dir or "-",
    )
