import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery
from aiogram_dialog import DialogManager, StartMode
from dishka.integrations.aiogram import inject, FromDishka

from src.application.mediator import Mediator
from src.application.use_cases.payment.confirm import ConfirmPaymentRequest
from src.application.use_cases.payment.get_by_external_id import (
    GetPaymentByExternalIdRequest,
)
from src.domain.entities.payment import Payment
from src.domain.enums.payment import PaymentStatus
from src.domain.exception.payment import PaymentNotFoundException
from src.application.use_cases.trainer.get_by_tg_id import GetTrainerByTgIdRequest
from src.domain.entities.trainer import Trainer
from src.domain.exception.trainer import TrainerNotFoundException
from src.infrastructure.notifications.callback_data.subscription import (
    RenewSubscriptionCD,
)

from .states import SubscriptionSG

logger = logging.getLogger(__name__)

router = Router(name="trainer_subscription")


@router.callback_query(RenewSubscriptionCD.filter())
@inject
async def on_renew_subscription_click(
    callback: CallbackQuery,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        trainer: Trainer = await mediator.handle(
            GetTrainerByTgIdRequest(tg_id=callback.from_user.id)
        )
    except TrainerNotFoundException:
        await callback.answer("Профиль тренера не найден", show_alert=True)
        return

    await callback.answer()
    await dialog_manager.start(
        state=SubscriptionSG.select_plan,
        mode=StartMode.RESET_STACK,
        data={"trainer_id": trainer.id},
    )


# --- Telegram Stars: payload инвойса == external_id платежа ---


@router.pre_checkout_query()
@inject
async def on_pre_checkout(query: PreCheckoutQuery, mediator: FromDishka[Mediator]) -> None:
    # последний шанс отказать до списания звёзд: платёж должен существовать
    # и ещё ждать оплаты (не оплачен повторно, не отклонён)
    try:
        payment: Payment = await mediator.handle(
            GetPaymentByExternalIdRequest(external_id=query.invoice_payload)
        )
    except PaymentNotFoundException:
        await query.answer(ok=False, error_message="Счёт не найден, создайте новый в боте.")
        return
    if payment.status != PaymentStatus.PENDING:
        await query.answer(ok=False, error_message="Этот счёт уже оплачен или отменён.")
        return
    await query.answer(ok=True)


@router.message(F.successful_payment)
@inject
async def on_successful_payment(message: Message, mediator: FromDishka[Mediator]) -> None:
    external_id = message.successful_payment.invoice_payload
    logger.info(
        "[Stars:successful_payment] external_id=%s amount=%s",
        external_id, message.successful_payment.total_amount,
    )
    try:
        await mediator.handle(ConfirmPaymentRequest(external_id=external_id))
    except Exception:
        logger.exception("[Stars:confirm_failed] external_id=%s", external_id)
        await message.answer(
            "❌ Оплата прошла, но подписку не удалось активировать автоматически. "
            "Администратор уже уведомлён — напишите ему, если доступ не появится."
        )
