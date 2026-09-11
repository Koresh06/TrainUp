from datetime import date

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, ChatEvent
from aiogram_dialog.widgets.kbd import Select, Button
from aiogram_dialog.widgets.kbd.calendar_kbd import ManagedCalendar

from src.application.mediator import Mediator
from src.application.use_cases.recurring_booking.add import AddRecurringBookingRequest
from src.presentation.telegram.widgets.booking_calendar import AVAILABILITY_CACHE_KEY


async def on_client_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["selected_client_id"] = int(item_id)
    await dialog_manager.next()


async def on_recurring_date_clicked(
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
        await callback.answer("На этот день нет открытых слотов", show_alert=True)
        return

    dialog_manager.dialog_data["selected_day"] = clicked_date.isoformat()
    await dialog_manager.next()


async def on_recurring_time_clicked(
    callback: CallbackQuery,
    widget: Select[str],
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["selected_slot_id"] = int(item_id)
    await dialog_manager.next()


@inject
async def on_recurring_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    client_id: int = dialog_manager.dialog_data["selected_client_id"]
    slot_id: int = dialog_manager.dialog_data["selected_slot_id"]

    await mediator.handle(
        AddRecurringBookingRequest(
            trainer_id=trainer_id,
            client_id=client_id,
            slot_id=slot_id,
        )
    )

    await callback.answer("Постоянная тренировка добавлена!", show_alert=True)
    await dialog_manager.done()
