from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode
from dishka.integrations.aiogram import inject, FromDishka

from src.application.mediator import Mediator
from src.application.use_cases.booking.get_by_id import GetBookingByIdRequest
from src.application.use_cases.client.get_by_tg_id import GetClientByTgIdRequest
from src.domain.entities.booking import Booking
from src.domain.entities.client import Client
from src.application.use_cases.booking.attendance import ConfirmAttendanceRequest
from src.application.use_cases.booking.rate import RateBookingRequest
from src.infrastructure.notifications.callback_data.rating import RateTrainingCD
from src.domain.exception.booking import BookingNotFoundException, BookingStatusTransitionException
from src.domain.exception.client import ClientNotFoundException
from src.infrastructure.notifications.callback_data.plan_next import PlanNextTrainingCD
from src.application.use_cases.booking.cancel import (
    CancelBookingRequest,
    CancelInitiator,
)
from src.infrastructure.notifications.callback_data.reminder import (
    ReminderAction,
    ReminderActionCD,
)
from src.presentation.telegram.features.client.booking.states import BookingSG
from src.presentation.telegram.features.client.menu.states import ClientMenuSG

router = Router()


@router.callback_query(ReminderActionCD.filter(F.action == ReminderAction.CONFIRM))
@inject
async def on_reminder_confirm(
    callback: CallbackQuery,
    callback_data: ReminderActionCD,
    mediator: FromDishka[Mediator],
) -> None:
    # «✅ Приду» — и в запросе накануне, и в напоминании: тренер видит 👍
    try:
        client: Client = await mediator.handle(
            GetClientByTgIdRequest(tg_id=callback.from_user.id)
        )
        await mediator.handle(
            ConfirmAttendanceRequest(booking_id=callback_data.booking_id, client_id=client.id)
        )
    except (ClientNotFoundException, BookingNotFoundException):
        await callback.answer("Это не ваша запись", show_alert=True)
        return
    except BookingStatusTransitionException:
        await callback.answer("Запись уже отменена или завершена", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        return
    await callback.answer("Отлично, ждём вас! 👍", show_alert=False)
    await callback.message.edit_text(f"{callback.message.html_text}\n\n👍 Вы подтвердили, что придёте")


@router.callback_query(ReminderActionCD.filter(F.action == ReminderAction.CANCEL))
@inject
async def on_reminder_cancel(
    callback: CallbackQuery,
    callback_data: ReminderActionCD,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        booking: Booking = await mediator.handle(
            GetBookingByIdRequest(booking_id=callback_data.booking_id)
        )
        client: Client = await mediator.handle(
            GetClientByTgIdRequest(tg_id=callback.from_user.id)
        )
    except (ClientNotFoundException, BookingNotFoundException):
        await callback.answer("Это не ваша запись", show_alert=True)
        return
    if booking.client_id != client.id:
        await callback.answer("Это не ваша запись", show_alert=True)
        return

    try:
        await mediator.handle(
            CancelBookingRequest(
                booking_id=callback_data.booking_id,
                initiated_by=CancelInitiator.CLIENT,
            )
        )
    except BookingStatusTransitionException:
        await callback.answer("Запись уже отменена или завершена", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        return
    await callback.answer("Запись отменена")
    await callback.message.edit_text("❌ Запись отменена")


@router.callback_query(PlanNextTrainingCD.filter())
@inject
async def on_plan_next_training_click(
    callback: CallbackQuery,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        client: Client = await mediator.handle(
            GetClientByTgIdRequest(tg_id=callback.from_user.id)
        )
    except ClientNotFoundException:
        await callback.answer("Профиль не найден", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    # меню кладём под календарь, чтобы после записи/«Назад» клиент попал в меню
    await dialog_manager.start(
        state=ClientMenuSG.main,
        data={"trainer_id": client.trainer_id},
        mode=StartMode.RESET_STACK,
    )
    await dialog_manager.start(
        state=BookingSG.select_day,
        data={"trainer_id": client.trainer_id},
    )


@router.callback_query(RateTrainingCD.filter())
@inject
async def on_rate_training(
    callback: CallbackQuery,
    callback_data: RateTrainingCD,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        client: Client = await mediator.handle(
            GetClientByTgIdRequest(tg_id=callback.from_user.id)
        )
        await mediator.handle(
            RateBookingRequest(
                booking_id=callback_data.booking_id,
                client_id=client.id,
                stars=callback_data.stars,
            )
        )
    except (ClientNotFoundException, BookingNotFoundException):
        await callback.answer("Это не ваша тренировка", show_alert=True)
        return
    except (BookingStatusTransitionException, ValueError):
        await callback.answer("Эту тренировку уже нельзя оценить", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        return
    await callback.answer("Спасибо!")
    await callback.message.edit_text(
        f"{callback.message.html_text}\n\nВаша оценка: {'⭐' * callback_data.stars} — спасибо!"
    )
