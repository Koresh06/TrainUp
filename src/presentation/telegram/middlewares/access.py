from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dishka import AsyncContainer
from dishka.integrations.aiogram import CONTAINER_NAME

from src.application.mediator import Mediator
from src.application.use_cases.access.get_user_access import (
    GetUserAccessRequest,
    UserAccessDTO,
)
from src.core.config import settings
from src.infrastructure.notifications.callback_data.subscription import (
    RenewSubscriptionCD,
)

USER_ACCESS_KEY = "user_access"

BLOCKED_TEXT = "⛔ Доступ к боту ограничен администратором."
TRAINER_UNAVAILABLE_TEXT = (
    "⛔ Запись к тренеру сейчас недоступна.\n"
    "Свяжитесь с тренером напрямую или попробуйте позже."
)
SUBSCRIPTION_EXPIRED_TEXT = (
    "⛔ <b>Подписка закончилась</b>\n\n"
    "Кабинет тренера и запись ваших клиентов приостановлены до продления."
)

Handler = Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]]


def is_admin(user: User | None) -> bool:
    return user is not None and user.id in settings.telegram.admin_ids


def renew_subscription_markup():
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Продлить подписку", callback_data=RenewSubscriptionCD().pack())
    return kb.as_markup()


async def _reply(event: TelegramObject, text: str, reply_markup=None) -> None:
    if isinstance(event, CallbackQuery):
        await event.answer()
        if event.message is not None:
            await event.message.answer(text, reply_markup=reply_markup)
    elif isinstance(event, Message):
        await event.answer(text, reply_markup=reply_markup)


class UserAccessMiddleware(BaseMiddleware):
    """
    Outer-middleware (после dishka): один раз на апдейт считает доступ
    пользователя, кладёт его в data[USER_ACCESS_KEY] для guard'ов и сразу
    отсекает тех, кого заблокировал админ. Админы не проверяются.
    """

    async def __call__(self, handler: Handler, event: TelegramObject, data: dict[str, Any]) -> Any:
        user: User | None = data.get("event_from_user")
        if user is None or is_admin(user):
            return await handler(event, data)

        # в рабочих группах тренера (кнопки подтверждения брони/заявок) проверка не нужна
        chat = data.get("event_chat")
        if chat is not None and chat.type != "private":
            return await handler(event, data)

        container: AsyncContainer = data[CONTAINER_NAME]
        mediator = await container.get(Mediator)
        access: UserAccessDTO = await mediator.handle(GetUserAccessRequest(tg_id=user.id))
        if access.is_blocked:
            await _reply(event, BLOCKED_TEXT)
            return None

        data[USER_ACCESS_KEY] = access
        return await handler(event, data)


class TrainerSubscriptionGuard(BaseMiddleware):
    """Inner-middleware на диалогах кабинета тренера: без активной подписки —
    сообщение и кнопка продления вместо действия."""

    async def __call__(self, handler: Handler, event: TelegramObject, data: dict[str, Any]) -> Any:
        access: UserAccessDTO | None = data.get(USER_ACCESS_KEY)
        if access is None or access.trainer is None or access.trainer_subscription_active:
            return await handler(event, data)
        await _reply(event, SUBSCRIPTION_EXPIRED_TEXT, renew_subscription_markup())
        return None


class ClientTrainerGuard(BaseMiddleware):
    """Inner-middleware на клиентских диалогах: если тренер клиента заблокирован
    или его подписка закончилась — клиент не может записываться и слать заявки."""

    async def __call__(self, handler: Handler, event: TelegramObject, data: dict[str, Any]) -> Any:
        access: UserAccessDTO | None = data.get(USER_ACCESS_KEY)
        if access is None or access.client is None or access.client_trainer_available:
            return await handler(event, data)
        await _reply(event, TRAINER_UNAVAILABLE_TEXT)
        return None


class AdminGuard(BaseMiddleware):
    """Inner-middleware на диалогах админки — защита от повтора чужих callback'ов."""

    async def __call__(self, handler: Handler, event: TelegramObject, data: dict[str, Any]) -> Any:
        if is_admin(data.get("event_from_user")):
            return await handler(event, data)
        if isinstance(event, CallbackQuery):
            await event.answer()
        return None
