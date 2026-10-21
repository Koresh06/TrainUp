"""DI: контейнер собирается, а каждый UseCaseRequest зарегистрирован в Mediator
(забыть mediator.register при добавлении use case — частая ошибка)."""

import importlib
import pkgutil

import src.application.use_cases as use_cases_pkg
from src.application.mediator import Mediator
from src.application.use_cases.base import UseCaseRequest


def _all_request_types() -> set[type]:
    for module in pkgutil.walk_packages(use_cases_pkg.__path__, use_cases_pkg.__name__ + "."):
        importlib.import_module(module.name)

    def subclasses(cls: type) -> set[type]:
        result = set()
        for sub in cls.__subclasses__():
            result |= {sub} | subclasses(sub)
        return result

    return subclasses(UseCaseRequest)


async def test_every_request_has_handler(container) -> None:
    async with container() as request_container:
        mediator = await request_container.get(Mediator)

    missing = sorted(
        cls.__name__
        for cls in _all_request_types()
        # тестовые запросы (например, в тестах Mediator) регистрировать не нужно
        if cls.__module__.startswith("src.") and cls not in mediator._handlers
    )
    assert missing == [], f"Не зарегистрированы в Mediator: {missing}"


def test_settings_ignore_foreign_env_file_keys(tmp_path, monkeypatch) -> None:
    # регресс: WEBHOOK_DOMAIN (для Caddy) в общем .env ронял старт приложения
    from src.core.config import Settings

    (tmp_path / ".env").write_text("WEBHOOK_DOMAIN=bot.example.com\nCOMPOSE_PROJECT_NAME=x\n")
    monkeypatch.chdir(tmp_path)
    Settings()
