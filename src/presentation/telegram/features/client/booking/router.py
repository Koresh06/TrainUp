from aiogram import Router, F
from aiogram.types import CallbackQuery

from dishka.integrations.aiogram import inject, FromDishka
from src.application.mediator import Mediator

from src.application.use_cases.booking.cancel import CancelBookingRequest
from src.application.use_cases.booking.confirm import ConfirmBookingRequest
from src.infrastructure.notifications.booking_callback_data import BookingAction, BookingActionCD


router = Router(name="trainer_actions")


@router.callback_query(BookingActionCD.filter(F.action == BookingAction.CONFIRM))
@inject
async def on_confirm_booking_click(
    callback: CallbackQuery,
    callback_data: BookingActionCD,
    mediator: FromDishka[Mediator],
) -> None:
    await mediator.handle(ConfirmBookingRequest(booking_id=callback_data.booking_id))
    await callback.answer("Подтверждено")
    await callback.message.edit_text(f"{callback.message.text}\n\n✅ Подтверждено")


@router.callback_query(BookingActionCD.filter(F.action == BookingAction.CANCEL))
@inject
async def on_cancel_booking_click(
    callback: CallbackQuery,
    callback_data: BookingActionCD,
    mediator: FromDishka[Mediator],
) -> None:
    await mediator.handle(CancelBookingRequest(booking_id=callback_data.booking_id))
    await callback.answer("Отменено")
    await callback.message.edit_text(f"{callback.message.text}\n\n❌ Отменено")