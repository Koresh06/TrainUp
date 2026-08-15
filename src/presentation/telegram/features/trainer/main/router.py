import logging

from dishka.integrations.aiogram import inject, FromDishka
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from src.domain.entities.trainer import Trainer
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.exception.trainer import TrainerNotFoundException
from src.application.mediator import Mediator
from src.application.use_cases.trainer.get_by_tg_id import GetTrainerByTgIdRequest
from src.application.use_cases.subscription.get_active import (
    GetActiveSubscriptionRequest,
)
from src.presentation.telegram.features.trainer.subscription.states import (
    SubscriptionSG,
    TrainerOnboardingSG,
)

from .states import TrainerMainSG

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("trainer"))
@inject
async def process_trainer_command(
    message: Message,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        trainer: Trainer = await mediator.handle(
            GetTrainerByTgIdRequest(tg_id=message.from_user.id)
        )
    except TrainerNotFoundException:
        await dialog_manager.start(
            state=TrainerOnboardingSG.welcome, mode=StartMode.RESET_STACK
        )
        return

    subscription: TrainerSubscription = await mediator.handle(
        GetActiveSubscriptionRequest(trainer_id=trainer.id)
    )

    if subscription is None:
        await dialog_manager.start(
            state=SubscriptionSG.select_plan,
            mode=StartMode.RESET_STACK,
            data={"trainer_id": trainer.id},
        )
        return

    await dialog_manager.start(
        state=TrainerMainSG.main,
        mode=StartMode.RESET_STACK,
        data={"trainer_id": trainer.id},
    )
