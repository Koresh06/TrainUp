from html import escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from dishka.integrations.aiogram import FromDishka, inject

from src.application.mediator import Mediator
from src.application.use_cases.payment.confirm import ConfirmPaymentRequest
from src.application.use_cases.payment.reject import RejectPaymentRequest
from src.application.use_cases.trainer.review import ReviewTrainerRequest
from src.domain.entities.bot_admin import AdminAccess
from src.domain.enums.admin import AdminPermission
from src.domain.exception.trainer import (
    TrainerAlreadyReviewedException,
    TrainerNotFoundException,
)
from src.domain.exception.payment import (
    PaymentNotFoundException,
    PaymentStatusTransitionException,
)
from src.infrastructure.notifications.callback_data.payment import (
    ManualPaymentAction,
    ManualPaymentCD,
)

from src.infrastructure.notifications.callback_data.trainer_approval import (
    TrainerApprovalAction,
    TrainerApprovalCD,
)
from src.presentation.telegram.middlewares.access import NO_PERMISSION_TEXT

from .states import AdminMenuSG

router = Router(name="admin")


@router.message(Command("admin"))
async def process_admin_command(
    message: Message,
    dialog_manager: DialogManager,
    admin_access: AdminAccess | None = None,
) -> None:
    if admin_access is None:
        return
    await dialog_manager.start(
        state=AdminMenuSG.main,
        mode=StartMode.RESET_STACK,
    )


@router.callback_query(TrainerApprovalCD.filter())
@inject
async def on_trainer_approval_action(
    callback: CallbackQuery,
    callback_data: TrainerApprovalCD,
    mediator: FromDishka[Mediator],
    admin_access: AdminAccess | None = None,
) -> None:
    if admin_access is None:
        await callback.answer()
        return
    if not admin_access.can(AdminPermission.TRAINERS_APPROVE):
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
        return

    approve = callback_data.action == TrainerApprovalAction.APPROVE
    try:
        await mediator.handle(
            ReviewTrainerRequest(
                trainer_id=callback_data.trainer_id,
                approve=approve,
                reviewed_by_tg_id=callback.from_user.id,
                only_pending=True,
            )
        )
    except (TrainerNotFoundException, TrainerAlreadyReviewedException):
        await callback.answer("Заявка уже обработана", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        return

    status = "✅ Тренер подтверждён" if approve else "❌ Заявка отклонена"
    await callback.answer(status)
    await callback.message.edit_text(
        f"{callback.message.html_text}\n\n<b>{status}</b> "
        f"({escape(callback.from_user.full_name)})",
        reply_markup=None,
    )


@router.callback_query(ManualPaymentCD.filter())
@inject
async def on_manual_payment_action(
    callback: CallbackQuery,
    callback_data: ManualPaymentCD,
    mediator: FromDishka[Mediator],
    admin_access: AdminAccess | None = None,
) -> None:
    if admin_access is None:
        await callback.answer()
        return
    if not admin_access.can(AdminPermission.PAYMENTS):
        await callback.answer(NO_PERMISSION_TEXT, show_alert=True)
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
