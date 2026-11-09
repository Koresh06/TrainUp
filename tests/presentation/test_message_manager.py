from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import EditMessageText

from src.presentation.telegram.message_manager import SafeMessageManager


def _bad_request(text: str) -> TelegramBadRequest:
    return TelegramBadRequest(
        method=EditMessageText(text="x"), message=f"Bad Request: {text}",
    )


async def test_resends_when_old_message_is_photo():
    manager = SafeMessageManager()
    manager.edit_message = AsyncMock(
        side_effect=_bad_request("there is no text in the message to edit"),
    )
    manager.remove_message_safe = AsyncMock()
    manager.send_message = AsyncMock(return_value="sent")

    result = await manager.edit_message_safe(AsyncMock(), "new", "old")

    assert result == "sent"
    manager.remove_message_safe.assert_awaited_once()
    manager.send_message.assert_awaited_once()


async def test_other_errors_are_raised():
    manager = SafeMessageManager()
    manager.edit_message = AsyncMock(side_effect=_bad_request("chat not found"))
    manager.send_message = AsyncMock()

    with pytest.raises(TelegramBadRequest):
        await manager.edit_message_safe(AsyncMock(), "new", "old")
    manager.send_message.assert_not_awaited()
