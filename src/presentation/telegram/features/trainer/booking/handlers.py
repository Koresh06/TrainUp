from datetime import date, timedelta
from typing import Any

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery
from aiogram_dialog import ChatEvent, DialogManager
from aiogram_dialog.widgets.kbd import Button, ManagedCalendar, Select

from src.application.mediator import Mediator
from src.application.use_cases.booking.cancel import (
    CancelBookingRequest,
    CancelInitiator,
)
from src.application.use_cases.booking.confirm import ConfirmBookingRequest
from src.application.use_cases.booking.create_by_trainer import (
    CreateBookingByTrainerRequest,
)
from src.application.use_cases.booking.get_by_id import GetBookingByIdRequest
from src.application.use_cases.booking.mark_attendance import (
    MarkBookingAttendanceRequest,
)
from src.application.use_cases.booking.reschedule import RescheduleBookingRequest
from src.domain.entities.booking import Booking
from src.domain.enums.booking import HistoryFilter
from src.domain.exception.booking import (
    BookingStatusTransitionException,
    ClientAlreadyBookedThisSlotException,
    SlotAlreadyBookedException,
    TrainingNotStartedException,
)
from src.domain.exception.calendar_slot import SlotFullException, SlotInPastException
from src.domain.utils import get_project_today
from src.presentation.telegram.features.trainer.clients.states import TrainerClientsSG
from src.presentation.telegram.widgets.booking_calendar import AVAILABILITY_CACHE_KEY

from .getters import (
    BOOKING_KEY,
    DAY_KEY,
    FILTER_KEY,
    MONTH_KEY,
    WEEK_KEY,
    current_day,
    shift_month,
)
from .states import TrainerBookingsSG

# откуда открыли запись — туда и возвращаемся по «Назад»
RETURN_KEY = "return_state"


async def on_schedule_start(start_data: Any, dialog_manager: DialogManager) -> None:
    # из утренней сводки / карточки клиента можно открыть конкретный день
    if isinstance(start_data, dict) and start_data.get("day"):
        dialog_manager.dialog_data[DAY_KEY] = start_data["day"]


def _set_day(dialog_manager: DialogManager, day: date) -> None:
    dialog_manager.dialog_data[DAY_KEY] = day.isoformat()


async def on_prev_day(callback: CallbackQuery, button: Button, dialog_manager: DialogManager) -> None:
    _set_day(dialog_manager, current_day(dialog_manager) - timedelta(days=1))


async def on_next_day(callback: CallbackQuery, button: Button, dialog_manager: DialogManager) -> None:
    _set_day(dialog_manager, current_day(dialog_manager) + timedelta(days=1))


async def on_today(callback: CallbackQuery, button: Button, dialog_manager: DialogManager) -> None:
    _set_day(dialog_manager, get_project_today())


async def on_open_week(callback: CallbackQuery, button: Button, dialog_manager: DialogManager) -> None:
    dialog_manager.dialog_data[WEEK_KEY] = current_day(dialog_manager).isoformat()
    await dialog_manager.switch_to(TrainerBookingsSG.week)


async def _shift_week(dialog_manager: DialogManager, days: int) -> None:
    raw = dialog_manager.dialog_data.get(WEEK_KEY)
    start = date.fromisoformat(raw) if raw else current_day(dialog_manager)
    dialog_manager.dialog_data[WEEK_KEY] = (start + timedelta(days=days)).isoformat()


async def on_prev_week(callback: CallbackQuery, button: Button, dialog_manager: DialogManager) -> None:
    await _shift_week(dialog_manager, -7)


async def on_next_week(callback: CallbackQuery, button: Button, dialog_manager: DialogManager) -> None:
    await _shift_week(dialog_manager, 7)


async def on_week_day_selected(
    callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str
) -> None:
    dialog_manager.dialog_data[DAY_KEY] = item_id
    await dialog_manager.switch_to(TrainerBookingsSG.day)


async def on_date_picked(
    callback: ChatEvent,
    widget: ManagedCalendar,
    dialog_manager: DialogManager,
    clicked_date: date,
    **kwargs,
) -> None:
    _set_day(dialog_manager, clicked_date)
    await dialog_manager.switch_to(TrainerBookingsSG.day)


# --- история ---


async def on_history_filter(
    callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str
) -> None:
    dialog_manager.dialog_data[FILTER_KEY] = HistoryFilter(item_id).value


async def on_prev_month(callback: CallbackQuery, button: Button, dialog_manager: DialogManager) -> None:
    dialog_manager.dialog_data[MONTH_KEY] = shift_month(dialog_manager.dialog_data.get(MONTH_KEY), -1)


async def on_next_month(callback: CallbackQuery, button: Button, dialog_manager: DialogManager) -> None:
    dialog_manager.dialog_data[MONTH_KEY] = shift_month(dialog_manager.dialog_data.get(MONTH_KEY), 1)


# --- карточка записи ---


async def on_booking_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data[BOOKING_KEY] = int(item_id)
    dialog_manager.dialog_data[RETURN_KEY] = dialog_manager.current_context().state.state
    await dialog_manager.switch_to(TrainerBookingsSG.detail)


async def on_detail_back(callback: CallbackQuery, button: Button, dialog_manager: DialogManager) -> None:
    await _back_from_detail(dialog_manager)


async def _back_from_detail(dialog_manager: DialogManager) -> None:
    state_name = dialog_manager.dialog_data.get(RETURN_KEY, TrainerBookingsSG.day.state)
    state = next(
        (s for s in TrainerBookingsSG.__states__ if s.state == state_name),
        TrainerBookingsSG.day,
    )
    await dialog_manager.switch_to(state)


@inject
async def on_confirm_booking(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        await mediator.handle(ConfirmBookingRequest(booking_id=dialog_manager.dialog_data[BOOKING_KEY]))
    except BookingStatusTransitionException:
        await callback.answer("Запись уже обработана или отменена", show_alert=True)
        return
    await callback.answer("✅ Подтверждено")


@inject
async def on_cancel_confirmed(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        await mediator.handle(
            CancelBookingRequest(
                booking_id=dialog_manager.dialog_data[BOOKING_KEY],
                initiated_by=CancelInitiator.TRAINER,
            )
        )
    except BookingStatusTransitionException:
        await callback.answer("Запись уже отменена или завершена", show_alert=True)
    else:
        await callback.answer("Тренировка отменена")
    await _back_from_detail(dialog_manager)


async def _mark_attendance(
    callback: CallbackQuery, dialog_manager: DialogManager, mediator: Mediator, attended: bool
) -> None:
    try:
        await mediator.handle(
            MarkBookingAttendanceRequest(
                trainer_id=dialog_manager.start_data["trainer_id"],
                booking_id=dialog_manager.dialog_data[BOOKING_KEY],
                attended=attended,
            )
        )
    except TrainingNotStartedException:
        await callback.answer("Тренировка ещё не началась", show_alert=True)
        return
    except BookingStatusTransitionException:
        await callback.answer("Статус записи уже изменился", show_alert=True)
        return
    await callback.answer("Отмечено")


@inject
async def on_no_show(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    await _mark_attendance(callback, dialog_manager, mediator, attended=False)


@inject
async def on_attended(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    await _mark_attendance(callback, dialog_manager, mediator, attended=True)


@inject
async def on_open_client_card(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    booking: Booking = await mediator.handle(
        GetBookingByIdRequest(booking_id=dialog_manager.dialog_data[BOOKING_KEY])
    )
    await dialog_manager.start(
        state=TrainerClientsSG.detail,
        data={"trainer_id": dialog_manager.start_data["trainer_id"], "client_id": booking.client_id},
    )


# --- перенос ---


async def on_reschedule_date_clicked(
    callback: ChatEvent,
    widget: ManagedCalendar,
    dialog_manager: DialogManager,
    clicked_date: date,
    **kwargs,
) -> None:
    availability: dict[str, int] = dialog_manager.dialog_data.get(AVAILABILITY_CACHE_KEY, {})
    if availability.get(clicked_date.isoformat(), 0) == 0:
        await callback.answer("На этот день нет свободных слотов", show_alert=True)
        return
    dialog_manager.dialog_data["reschedule_day"] = clicked_date.isoformat()
    await dialog_manager.switch_to(TrainerBookingsSG.reschedule_time)


async def on_reschedule_time_clicked(
    callback: CallbackQuery,
    widget: Select[str],
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["new_slot_id"] = int(item_id)
    await dialog_manager.switch_to(TrainerBookingsSG.reschedule_confirm)


@inject
async def on_reschedule_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        await mediator.handle(
            RescheduleBookingRequest(
                booking_id=dialog_manager.dialog_data[BOOKING_KEY],
                new_slot_id=dialog_manager.dialog_data["new_slot_id"],
            )
        )
    except SlotFullException:
        await callback.answer("Мест не осталось на этом слоте", show_alert=True)
        return
    except (SlotAlreadyBookedException, SlotInPastException):
        await callback.answer("Этот слот уже недоступен", show_alert=True)
        return
    except BookingStatusTransitionException:
        await callback.answer("Запись уже отменена или завершена", show_alert=True)
        await _back_from_detail(dialog_manager)
        return

    await callback.answer("Перенесено!", show_alert=True)
    await dialog_manager.switch_to(TrainerBookingsSG.detail)


# --- записать клиента на день ---


async def on_add_client_selected(
    callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str
) -> None:
    dialog_manager.dialog_data["add_client_id"] = int(item_id)
    await dialog_manager.switch_to(TrainerBookingsSG.add_time)


async def on_add_time_selected(
    callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str
) -> None:
    dialog_manager.dialog_data["add_slot_id"] = int(item_id)
    await dialog_manager.switch_to(TrainerBookingsSG.add_confirm)


@inject
async def on_add_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    try:
        await mediator.handle(
            CreateBookingByTrainerRequest(
                trainer_id=dialog_manager.start_data["trainer_id"],
                client_id=dialog_manager.dialog_data["add_client_id"],
                slot_id=dialog_manager.dialog_data["add_slot_id"],
            )
        )
    except ClientAlreadyBookedThisSlotException:
        await callback.answer("Клиент уже записан на это время", show_alert=True)
        return
    except (SlotFullException, SlotAlreadyBookedException, SlotInPastException):
        await callback.answer("Это время уже недоступно", show_alert=True)
        await dialog_manager.switch_to(TrainerBookingsSG.add_time)
        return
    await callback.answer("✅ Клиент записан")
    await dialog_manager.switch_to(TrainerBookingsSG.day)
