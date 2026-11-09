from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from aiogram_dialog.api.entities import NewMessage, OldMessage
from aiogram_dialog.manager.message_manager import MessageManager


class SafeMessageManager(MessageManager):
    """Пересылает сообщение, если старое нельзя отредактировать из-за типа.

    aiogram-dialog узнаёт тип старого сообщения из callback. Если Telegram
    прислал InaccessibleMessage (сообщение старше 48 часов), библиотека
    считает его текстовым и вызывает edit_message_text даже для фото
    (график, фото профиля). Telegram отвечает "there is no text in the
    message to edit". В таком случае удаляем старое и шлём новое.
    """

    async def edit_message_safe(
        self, bot: Bot, new_message: NewMessage, old_message: OldMessage,
    ) -> Message:
        try:
            return await super().edit_message_safe(bot, new_message, old_message)
        except TelegramBadRequest as err:
            if not _is_wrong_content_type(err.message):
                raise
            await self.remove_message_safe(bot, old_message, new_message)
            return await self.send_message(bot, new_message)


def _is_wrong_content_type(message: str) -> bool:
    # "there is no text/media/caption in the message to edit"
    return "there is no" in message and "in the message to edit" in message
