from aiogram import Router, F
from aiogram.types import CallbackQuery

from dishka.integrations.aiogram import inject, FromDishka
from src.application.mediator import Mediator

from src.application.use_cases.booking.cancel import CancelBookingRequest, CancelInitiator
from src.application.use_cases.booking.confirm import ConfirmBookingRequest
from src.domain.exception.booking import BookingStatusTransitionException
from src.infrastructure.notifications.callback_data.booking import BookingAction, BookingActionCD


router = Router(name="trainer_actions")


@router.callback_query(BookingActionCD.filter(F.action == BookingAction.CONFIRM))
@inject
async def on_confirm_booking_click(
    callback: CallbackQuery,
    callback_data: BookingActionCD,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        await mediator.handle(ConfirmBookingRequest(booking_id=callback_data.booking_id))
    except BookingStatusTransitionException:
        await callback.answer("Запись уже обработана или отменена", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        return
    await callback.answer("Подтверждено")
    await callback.message.edit_text(f"{callback.message.html_text}\n\n✅ Подтверждено")


@router.callback_query(BookingActionCD.filter(F.action == BookingAction.CANCEL))
@inject
async def on_cancel_booking_click(
    callback: CallbackQuery,
    callback_data: BookingActionCD,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        await mediator.handle(
            CancelBookingRequest(
                booking_id=callback_data.booking_id,
                initiated_by=CancelInitiator.TRAINER,
            )
        )
    except BookingStatusTransitionException:
        await callback.answer("Запись уже обработана или отменена", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        return
    await callback.answer("Отменено")
    await callback.message.edit_text(f"{callback.message.html_text}\n\n❌ Отменено")