from dishka.integrations.aiogram import inject, FromDishka
from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from src.application.mediator import Mediator
from src.application.use_cases.client.get_by_tg_id import GetClientByTgIdRequest
from src.application.use_cases.invite_link.resolve import ResolveInviteLinkRequest
from src.domain.entities.client import Client
from src.domain.entities.trainer_invite_link import TrainerInviteLink
from src.domain.exception.client import ClientNotFoundException
from src.domain.exception.invite_link import (
    TrainerInviteLinkInactiveException,
    TrainerInviteLinkNotFoundException,
)
from src.presentation.telegram.features.client.register.states import ClientRegisterSG
from src.presentation.telegram.features.client.menu.states import ClientMenuSG

router = Router()


@router.message(CommandStart(deep_link=True))
@inject
async def process_start_with_token(
    message: Message,
    command: CommandObject,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    token = command.args

    try:
        link: TrainerInviteLink = await mediator.handle(
            ResolveInviteLinkRequest(token=token)
        )
    except (TrainerInviteLinkNotFoundException, TrainerInviteLinkInactiveException):
        await message.answer(
            "🚫 Эта ссылка недействительна или устарела.\n"
            "Доступ к боту возможен только по актуальной ссылке от тренера."
        )
        return

    try:
        await mediator.handle(GetClientByTgIdRequest(tg_id=message.from_user.id))
    except ClientNotFoundException:
        await dialog_manager.start(
            state=ClientRegisterSG.welcome,
            data={"trainer_id": link.trainer_id},
            mode=StartMode.RESET_STACK,
        )
        return

    await dialog_manager.start(
        state=ClientMenuSG.main,
        data={"trainer_id": link.trainer_id},
        mode=StartMode.RESET_STACK,
    )


@router.message(CommandStart(deep_link=False))
@inject
async def process_start_plain(
    message: Message,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        client: Client = await mediator.handle(
            GetClientByTgIdRequest(tg_id=message.from_user.id)
        )
    except ClientNotFoundException:
        await message.answer(
            "🚫 Доступ к боту возможен только по персональной ссылке от тренера.\n"
            "Попроси тренера отправить тебе ссылку для регистрации."
        )
        return

    await dialog_manager.start(
        state=ClientMenuSG.main,
        data={"trainer_id": client.trainer_id},
        mode=StartMode.RESET_STACK,
    )
