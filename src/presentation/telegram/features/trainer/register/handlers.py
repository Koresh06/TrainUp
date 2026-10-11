from aiogram.exceptions import TelegramAPIError
from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import (
    CallbackQuery,
    Message,
    MessageOriginChannel,
    MessageOriginChat,
)
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Select, Button
from aiogram_dialog.widgets.input import MessageInput

from src.domain.entities.trainer import Trainer
from src.domain.exception.trainer import TrainerAlreadyExistsException
from src.application.mediator import Mediator
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.application.use_cases.subscription.get_active import (
    GetActiveSubscriptionRequest,
)
from src.application.use_cases.payment.create_subscription_payment import (
    CreatedPaymentDTO,
    CreateSubscriptionPaymentRequest,
)
from src.domain.enums.payment import PaymentMethod, PaymentStatus
from src.domain.exception.payment import (
    PaymentAmountInvalidException,
    PaymentProviderNotFoundException,
    PaymentProviderUnavailableException,
)
from src.presentation.telegram.features.trainer.main.states import TrainerMainSG

from .states import SubscriptionSG


async def on_photo_received(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data["photo_file_id"] = message.photo[-1].file_id


async def on_delete_photo(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
) -> None:
    if "photo_file_id" in dialog_manager.dialog_data:
        dialog_manager.dialog_data.pop("photo_file_id")
        await callback.answer("Фото удалено. Отправьте новое.")
    else:
        await callback.answer("Фото для удаления не найдено.", show_alert=True)


async def _save_notification_chat(
    message: Message,
    dialog_manager: DialogManager,
    chat_id: int,
    title: str | None,
    username: str | None,
) -> None:
    dialog_manager.dialog_data["notification_chat_id"] = chat_id
    dialog_manager.dialog_data["group_title"] = title

    invite_link: str | None = None
    try:
        invite_link = await message.bot.export_chat_invite_link(chat_id)
    except TelegramAPIError:
        if username:
            invite_link = f"https://t.me/{username}"

    dialog_manager.dialog_data["group_invite_link"] = invite_link
    await dialog_manager.next()


async def on_group_chat_shared(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
) -> None:
    shared = message.chat_shared
    await _save_notification_chat(
        message, dialog_manager, shared.chat_id, shared.title, shared.username
    )


async def on_group_message_forwarded(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
) -> None:
    # Bot API 7+: источник пересылки — forward_origin (forward_from_chat устарел)
    origin = message.forward_origin
    chat = None
    if isinstance(origin, MessageOriginChannel):
        chat = origin.chat
    elif isinstance(origin, MessageOriginChat):
        chat = origin.sender_chat
    if chat is None or chat.type not in ("group", "supergroup", "channel"):
        await message.answer(
            "Это не похоже на пересланное сообщение из группы/канала. Попробуй ещё раз.\n"
            "Для группы: включите анонимную отправку админа или используйте канал."
        )
        return
    await _save_notification_chat(
        message, dialog_manager, chat.id, chat.title, chat.username
    )


@inject
async def on_onboarding_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> None:
    data = dialog_manager.dialog_data

    try:
        trainer: Trainer = await mediator.handle(
            RegisterTrainerRequest(
                tg_id=callback.from_user.id,
                name=dialog_manager.find("name").get_value(),
                bio=dialog_manager.find("bio").get_value(),
                notification_chat_id=data["notification_chat_id"],
                photo_file_id=data.get("photo_file_id"),
                phone=data.get("phone"),
            )
        )
    except TrainerAlreadyExistsException:
        # повторное нажатие «Завершить» — профиль уже создан
        await callback.answer(
            "Профиль уже создан — откройте кабинет командой /trainer",
            show_alert=True,
        )
        await dialog_manager.done()
        return

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
async def on_payment_method_selected(
    callback: CallbackQuery,
    widget: Select[str],
    dialog_manager: DialogManager,
    item_id: str,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        created: CreatedPaymentDTO = await mediator.handle(
            CreateSubscriptionPaymentRequest(
                trainer_id=dialog_manager.start_data["trainer_id"],
                price_plan_id=dialog_manager.dialog_data["price_plan_id"],
                method=PaymentMethod(item_id),
            )
        )
    except PaymentProviderUnavailableException:
        await callback.answer(
            "⚠️ Платёжная система временно недоступна. Попробуйте позже "
            "или выберите другой способ оплаты.",
            show_alert=True,
        )
        return
    except (PaymentAmountInvalidException, PaymentProviderNotFoundException):
        await callback.answer(
            "⚠️ Этот способ оплаты сейчас недоступен — выберите другой.",
            show_alert=True,
        )
        return

    dialog_manager.dialog_data["payment_instructions"] = created.instructions.text
    dialog_manager.dialog_data["payment_url"] = created.instructions.url
    dialog_manager.dialog_data["payment_paid"] = created.payment.status == PaymentStatus.PAID
    await dialog_manager.switch_to(SubscriptionSG.payment)


@inject
async def on_back_to_cabinet(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    subscription = await mediator.handle(GetActiveSubscriptionRequest(trainer_id=trainer_id))
    if subscription is None:
        await callback.answer(
            "Кабинет откроется после оплаты подписки", show_alert=True
        )
        return
    await dialog_manager.start(
        state=TrainerMainSG.main,
        mode=StartMode.RESET_STACK,
        data={"trainer_id": trainer_id},
    )
