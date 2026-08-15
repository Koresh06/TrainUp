import logging

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.core.config import settings
from src.application.mediator import Mediator
from src.application.use_cases.invite_link.get_active import (
    GetActiveInviteLinkRequest,
)
from src.domain.entities.trainer_invite_link import TrainerInviteLink
from src.domain.exception.invite_link import TrainerInviteLinkNotFoundException

logger = logging.getLogger(__name__)


@inject
async def invite_link_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = int(dialog_manager.start_data["trainer_id"])

    link: TrainerInviteLink = await mediator.handle(
        GetActiveInviteLinkRequest(trainer_id=trainer_id)
    )
    link_url = f"https://t.me/{settings.telegram.bot_username}?start={link.token}"
    return {"link_url": link_url}