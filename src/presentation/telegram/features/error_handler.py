import logging

from aiogram import Dispatcher
from aiogram.types import ErrorEvent, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.api.exceptions import OutdatedIntent, UnknownIntent, UnknownState
from aiogram_dialog.widgets.input import ManagedTextInput

from src.domain.exception.base import DomainError
from src.presentation.telegram.middlewares.logging_context import describe_update

logger = logging.getLogger(__name__)

OUTDATED_MENU_TEXT = (
    "⌛ Это меню устарело — откройте его заново: /start (клиент) или /trainer (тренер)."
)
UNEXPECTED_ERROR_TEXT = (
    "😔 Что-то пошло не так. Попробуйте ещё раз или откройте меню заново: /start"
)


async def on_input_error(
    message: Message,
    widget: ManagedTextInput[str],
    dialog_manager: DialogManager,
    error: ValueError,
) -> None:
    await message.answer(f"❌ {error}")


async def _reply(event: ErrorEvent, text: str) -> None:
    update = event.update
    try:
        if update.callback_query is not None:
            await update.callback_query.answer(text, show_alert=True)
        elif update.message is not None:
            await update.message.answer(text)
    except Exception:  # ответить не удалось — главное, что ошибка уже в логе
        logger.debug("[ErrorHandler] reply failed", exc_info=True)


async def on_error(event: ErrorEvent) -> bool:
    """
    Последний рубеж: всё, что не поймали хендлеры. Пишем в лог с полным
    traceback и тем, кто/что нажал, а пользователю — понятный ответ вместо тишины.
    """
    error = event.exception
    user_id, action = describe_update(event.update)

    if isinstance(error, (UnknownIntent, OutdatedIntent, UnknownState)):
        # нажали кнопку старого сообщения (бот перезапускался / стек сброшен)
        logger.warning("[ErrorHandler] outdated dialog u=%s %s: %s", user_id, action, error)
        await _reply(event, OUTDATED_MENU_TEXT)
        return True

    if isinstance(error, DomainError):
        # бизнес-правило не пропустило, а хендлер это не обработал — баг UI,
        # но не авария: пользователю — понятный текст ошибки
        logger.warning(
            "[ErrorHandler] unhandled domain error u=%s %s: %s",
            user_id, action, error.message, exc_info=error,
        )
        await _reply(event, f"⚠️ {error.message}")
        return True

    logger.error(
        "[ErrorHandler] unexpected error u=%s %s update_id=%s",
        user_id, action, event.update.update_id, exc_info=error,
    )
    await _reply(event, UNEXPECTED_ERROR_TEXT)
    return True


def setup_error_handling(dp: Dispatcher) -> None:
    dp.errors.register(on_error)
