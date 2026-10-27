from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from dishka.integrations.aiogram import FromDishka, inject

from src.application.mediator import Mediator
from src.application.use_cases.payment.confirm import ConfirmPaymentRequest
from src.application.use_cases.payment.reject import RejectPaymentRequest
from src.domain.exception.payment import (
    PaymentNotFoundException,
    PaymentStatusTransitionException,
)
from src.infrastructure.notifications.callback_data.payment import (
    ManualPaymentAction,
    ManualPaymentCD,
)

from src.presentation.telegram.middlewares.access import is_admin

from .states import AdminMenuSG

router = Router(name="admin")


@router.message(Command("admin"))
async def process_admin_command(
    message: Message, dialog_manager: DialogManager
) -> None:
    if not is_admin(message.from_user):
        return
    await dialog_manager.start(
        state=AdminMenuSG.main,
        mode=StartMode.RESET_STACK,
    )


@router.callback_query(ManualPaymentCD.filter())
@inject
async def on_manual_payment_action(
    callback: CallbackQuery,
    callback_data: ManualPaymentCD,
    mediator: FromDishka[Mediator],
) -> None:
    if not is_admin(callback.from_user):
        await callback.answer()
        return

    approve = callback_data.action == ManualPaymentAction.APPROVE
    try:
        if approve:
            await mediator.handle(
                ConfirmPaymentRequest(external_id=callback_data.external_id)
            )
        else:
            await mediator.handle(
                RejectPaymentRequest(
                    external_id=callback_data.external_id, notify_trainer=True
                )
            )
    except (PaymentNotFoundException, PaymentStatusTransitionException):
        await callback.answer("Заявка уже обработана", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        return

    who = callback.from_user.full_name
    status = (
        "✅ Оплата подтверждена, подписка активирована" if approve else "❌ Отклонено"
    )
    await callback.answer(status)
    await callback.message.edit_text(
        f"{callback.message.html_text}\n\n<b>{status}</b> ({who})",
        reply_markup=None,
    )
