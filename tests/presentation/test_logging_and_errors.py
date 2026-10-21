"""Логирование: контекст апдейта, общий обработчик ошибок, Mediator."""

import logging
from dataclasses import dataclass
from datetime import datetime

import pytest
from aiogram.types import CallbackQuery, Chat, ErrorEvent, Message, Update, User
from aiogram_dialog.api.exceptions import UnknownIntent

from src.application.mediator import Mediator
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.exception.client import ClientNotFoundException
from src.presentation.telegram.features.error_handler import on_error
from src.presentation.telegram.middlewares.logging_context import describe_update

USER = User(id=42, is_bot=False, first_name="Тест")
CHAT = Chat(id=42, type="private")


def message(text: str) -> Update:
    return Update(update_id=1, message=Message(message_id=1, date=datetime.now(), chat=CHAT, from_user=USER, text=text))


def callback(data: str) -> Update:
    return Update(update_id=2, callback_query=CallbackQuery(id="1", from_user=USER, chat_instance="x", data=data))


def test_describe_update_hides_message_text() -> None:
    assert describe_update(message("/start cl_abc")) == (42, "cmd=/start")
    assert describe_update(message("+375291234567")) == (42, "text[13]")
    assert describe_update(callback("Ab12\x1dbooking_calendar:1")) == (42, "cb=Ab12/booking_calendar:1")


async def test_outdated_dialog_is_warning(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        assert await on_error(ErrorEvent(update=callback("old"), exception=UnknownIntent("gone")))
    assert "outdated dialog u=42 cb=old" in caplog.text


async def test_unexpected_error_logged_with_traceback(caplog) -> None:
    with caplog.at_level(logging.ERROR):
        assert await on_error(ErrorEvent(update=message("/trainer"), exception=KeyError("MONTHS")))
    [record] = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert "u=42 cmd=/trainer" in record.getMessage() and record.exc_info is not None


@dataclass(frozen=True, eq=False)
class BoomRequest(UseCaseRequest):
    value: int


class BoomUseCase(UseCase[BoomRequest, None]):
    async def __call__(self, command: BoomRequest) -> None:
        if command.value == 1:
            raise ClientNotFoundException(client_id=1)
        raise RuntimeError("boom")


async def test_mediator_logs_failures(caplog) -> None:
    mediator = Mediator()
    mediator.register(BoomRequest, BoomUseCase())
    with caplog.at_level(logging.INFO):
        with pytest.raises(ClientNotFoundException):
            await mediator.handle(BoomRequest(value=1))
        with pytest.raises(RuntimeError):
            await mediator.handle(BoomRequest(value=2))
    assert "BoomRequest rejected: Клиент с id 1 не найден" in caplog.text
    [error] = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert "BoomRequest failed" in error.getMessage() and "value=2" in error.getMessage()
