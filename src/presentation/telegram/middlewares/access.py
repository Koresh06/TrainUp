from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dishka import AsyncContainer
from dishka.integrations.aiogram import CONTAINER_NAME

from src.application.mediator import Mediator
from src.application.use_cases.staff.get_access import GetAdminAccessRequest
from src.application.use_cases.access.get_user_access import (
    GetUserAccessRequest,
    UserAccessDTO,
)
from src.domain.entities.bot_admin import AdminAccess
from src.domain.enums.admin import AdminPermission
from src.infrastructure.notifications.callback_data.subscription import (
    RenewSubscriptionCD,
)

USER_ACCESS_KEY = "user_access"
ADMIN_ACCESS_KEY = "admin_access"

NO_PERMISSION_TEXT = "⛔ Недостаточно прав. Доступ выдаёт супер-администратор."
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
    отсекает тех, кого заблокировал админ. Права админа — в data[ADMIN_ACCESS_KEY].
    Супер-админ не проверяется вовсе, а обычный админ — только на блокировку:
    если он ещё и тренер, подписка для кабинета ему всё равно нужна.
    """

    async def __call__(self, handler: Handler, event: TelegramObject, data: dict[str, Any]) -> Any:
        user: User | None = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        container: AsyncContainer = data[CONTAINER_NAME]
        mediator = await container.get(Mediator)
        admin: AdminAccess | None = await mediator.handle(
            GetAdminAccessRequest(tg_id=user.id)
        )
        data[ADMIN_ACCESS_KEY] = admin
        if admin is not None and admin.is_super:
            return await handler(event, data)

        # в рабочих группах тренера (кнопки подтверждения брони/заявок) проверка не нужна
        chat = data.get("event_chat")
        if chat is not None and chat.type != "private":
            return await handler(event, data)

        access: UserAccessDTO = await mediator.handle(GetUserAccessRequest(tg_id=user.id))
        if access.is_blocked and admin is None:
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
    """Inner-middleware на диалогах админки — защита от чужих callback'ов и от
    действий в окне, открытом до того, как право отозвали. Без permissions
    раздел открыт любому админу, с ними — тому, у кого есть хотя бы одно."""

    def __init__(self, *permissions: AdminPermission, super_only: bool = False) -> None:
        self.permissions = permissions
        self.super_only = super_only

    def _allowed(self, admin: AdminAccess) -> bool:
        if self.super_only:
            return admin.is_super
        return not self.permissions or admin.can(*self.permissions)

    async def __call__(self, handler: Handler, event: TelegramObject, data: dict[str, Any]) -> Any:
        admin: AdminAccess | None = data.get(ADMIN_ACCESS_KEY)
        if admin is not None and self._allowed(admin):
            return await handler(event, data)
        if isinstance(event, CallbackQuery):
            if admin is not None:
                await event.answer(NO_PERMISSION_TEXT, show_alert=True)
            else:
                await event.answer()
        return None
