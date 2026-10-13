
from aiogram import F, Router
from aiogram.filters import KICKED, MEMBER, ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated
from dishka.integrations.aiogram import FromDishka, inject

from src.application.mediator import Mediator
from src.application.use_cases.bot_user.set_bot_blocked import SetBotBlockedByUserRequest


router = Router(name="bot_status")
# только личные чаты: в группах my_chat_member — это добавление/удаление бота
# из рабочей группы тренера, а не блокировка пользователем
router.my_chat_member.filter(F.chat.type == "private")


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
@inject
async def on_bot_blocked(event: ChatMemberUpdated, mediator: FromDishka[Mediator]) -> None:
    await mediator.handle(SetBotBlockedByUserRequest(tg_id=event.from_user.id, blocked=True))


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
@inject
async def on_bot_unblocked(event: ChatMemberUpdated, mediator: FromDishka[Mediator]) -> None:
    await mediator.handle(SetBotBlockedByUserRequest(tg_id=event.from_user.id, blocked=False))
