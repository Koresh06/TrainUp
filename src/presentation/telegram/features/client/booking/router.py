from aiogram import Router, F
from aiogram.types import CallbackQuery
from dishka.integrations.aiogram import inject, FromDishka

from src.application.mediator import Mediator
from src.application.use_cases.booking.cancel import (
    CancelBookingRequest,
    CancelInitiator,
)
from src.infrastructure.notifications.callback_data.reminder import (
    ReminderAction,
    ReminderActionCD,
)

router = Router()


@router.callback_query(ReminderActionCD.filter(F.action == ReminderAction.CONFIRM))
async def on_reminder_confirm(
    callback: CallbackQuery,
    callback_data: ReminderActionCD,
) -> None:
    await callback.answer("Отлично, ждём вас! 👍", show_alert=False)
    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(ReminderActionCD.filter(F.action == ReminderAction.CANCEL))
@inject
async def on_reminder_cancel(
    callback: CallbackQuery,
    callback_data: ReminderActionCD,
    mediator: FromDishka[Mediator],
) -> None:
    await mediator.handle(
        CancelBookingRequest(
            booking_id=callback_data.booking_id,
            initiated_by=CancelInitiator.CLIENT,
        )
    )
    await callback.answer("Запись отменена")
    await callback.message.edit_text("❌ Запись отменена")
