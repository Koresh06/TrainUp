from datetime import date

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import ChatEvent, DialogManager
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import ManagedCalendar, Select, Button

from src.application.mediator import Mediator
from src.application.use_cases.booking.cancel import (
    CancelBookingRequest,
    CancelInitiator,
)
from src.application.use_cases.booking.reschedule import RescheduleBookingRequest
from src.domain.exception.calendar_slot import SlotFullException
from src.presentation.telegram.widgets.booking_calendar import AVAILABILITY_CACHE_KEY

from .states import TrainerBookingsSG


async def on_booking_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["editing_booking_id"] = int(item_id)
    await dialog_manager.next()


def is_not_recurring(data: dict, widget, manager: DialogManager) -> bool:
    return not data.get("is_recurring", False)


async def on_reschedule_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.next()


@inject
async def on_cancel_booking_from_list(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    booking_id: int = dialog_manager.dialog_data["editing_booking_id"]
    await mediator.handle(
        CancelBookingRequest(
            booking_id=booking_id,
            initiated_by=CancelInitiator.TRAINER,
        )
    )
    await callback.answer("Отменено")
    await dialog_manager.switch_to(TrainerBookingsSG.list)


async def on_reschedule_date_clicked(
    callback: ChatEvent,
    widget: ManagedCalendar,
    dialog_manager: DialogManager,
    clicked_date: date,
    **kwargs,
) -> None:
    availability: dict[str, int] = dialog_manager.dialog_data.get(
        AVAILABILITY_CACHE_KEY, {}
    )
    if availability.get(clicked_date.isoformat(), 0) == 0:
        await callback.answer("На этот день нет свободных слотов", show_alert=True)
        return
    dialog_manager.dialog_data["reschedule_day"] = clicked_date.isoformat()
    await dialog_manager.next()


async def on_reschedule_time_clicked(
    callback: CallbackQuery,
    widget: Select[str],
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["new_slot_id"] = int(item_id)
    await dialog_manager.next()


@inject
async def on_reschedule_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    booking_id: int = dialog_manager.dialog_data["editing_booking_id"]
    new_slot_id: int = dialog_manager.dialog_data["new_slot_id"]

    try:
        await mediator.handle(
            RescheduleBookingRequest(
                booking_id=booking_id,
                new_slot_id=new_slot_id,
            )
        )
    except SlotFullException:
        await callback.answer("Мест не осталось на этом слоте", show_alert=True)
        return

    await callback.answer("Перенесено!", show_alert=True)
    await dialog_manager.switch_to(TrainerBookingsSG.list)
