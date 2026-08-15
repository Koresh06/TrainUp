from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Select, Button
from aiogram_dialog.widgets.input import MessageInput

from src.domain.entities.trainer import Trainer
from src.utils.timezone import to_moscow
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.application.mediator import Mediator
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.application.use_cases.subscription.purchse import PurchaseSubscriptionRequest
from src.presentation.telegram.features.trainer.main.states import TrainerMainSG

from .states import SubscriptionSG, TrainerOnboardingSG


async def on_group_message_forwarded(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
) -> None:
    if message.forward_from_chat is None or message.forward_from_chat.type not in (
        "group", "supergroup", "channel",
    ):
        await message.answer("Это не похоже на пересланное сообщение из группы/канала. Попробуй ещё раз.")
        return
    chat = message.forward_from_chat
    dialog_manager.dialog_data["notification_chat_id"] = chat.id
    dialog_manager.dialog_data["group_title"] = chat.title

    invite_link: str | None = None
    try:
        invite_link = await message.bot.export_chat_invite_link(chat.id)
    except TelegramAPIError:
        if chat.username:
            invite_link = f"https://t.me/{chat.username}"

    dialog_manager.dialog_data["group_invite_link"] = invite_link
    await dialog_manager.next()


@inject
async def on_onboarding_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> None:
    data = dialog_manager.dialog_data

    trainer: Trainer = await mediator.handle(
        RegisterTrainerRequest(
            tg_id=callback.from_user.id,
            name=dialog_manager.find("name").get_value(),
            bio=dialog_manager.find("bio").get_value(),
            notification_chat_id=data["notification_chat_id"],
        )
    )

    await callback.answer()
    await dialog_manager.start(
        state=SubscriptionSG.select_plan,
        mode=StartMode.RESET_STACK,
        data={"trainer_id": trainer.id},
    )

async def on_plan_selected(
    callback: CallbackQuery,
    widget: Select[str],
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["price_plan_id"] = int(item_id)
    await dialog_manager.next()


@inject
async def on_confirm_purchase(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    price_plan_id: int = dialog_manager.dialog_data["price_plan_id"]

    subscription: TrainerSubscription = await mediator.handle(
        PurchaseSubscriptionRequest(trainer_id=trainer_id, price_plan_id=price_plan_id)
    )

    await callback.answer()
    await callback.answer(
        f"🎉 Готово! Подписка активна до "
        f"{to_moscow(subscription.expired_at).strftime('%d.%m.%Y')}.",
        show_alert=True,
    )
    await dialog_manager.start(
        state=TrainerMainSG.main,
        mode=StartMode.RESET_STACK,
        data={"trainer_id": trainer_id},
    )