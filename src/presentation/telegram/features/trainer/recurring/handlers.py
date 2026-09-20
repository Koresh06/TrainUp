from datetime import date

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, ChatEvent
from aiogram_dialog.widgets.kbd import Select, Button
from aiogram_dialog.widgets.kbd.calendar_kbd import ManagedCalendar

from src.application.mediator import Mediator
from src.application.use_cases.recurring_booking.add import AddRecurringBookingRequest
from src.application.use_cases.recurring_booking.change import (
    ChangeRecurringBookingScheduleRequest,
)
from src.application.use_cases.recurring_booking.deactivate import (
    DeactivateRecurringBookingRequest,
)
from src.domain.exception.calendar_slot import SlotFullException
from src.domain.exception.recurring_booking import (
    RecurringBookingAlreadyExistsException,
)
from src.presentation.telegram.features.trainer.recurring.states import (
    TrainerRecurringSG,
)
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

    try:
        await mediator.handle(
            AddRecurringBookingRequest(
                trainer_id=trainer_id,
                client_id=client_id,
                slot_id=slot_id,
            )
        )
    except RecurringBookingAlreadyExistsException:
        await callback.answer(
            "У этого клиента уже есть постоянная запись на это время.",
            show_alert=True,
        )
        return

    await callback.answer("Постоянная тренировка добавлена!", show_alert=True)
    await dialog_manager.done()


async def on_recurring_client_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["selected_client_id"] = int(item_id)
    await dialog_manager.next()


@inject
async def on_recurring_item_selected(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["editing_recurring_id"] = int(item_id)
    await dialog_manager.switch_to(TrainerRecurringSG.detail)


@inject
async def on_deactivate_recurring_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    recurring_id: int = dialog_manager.dialog_data["editing_recurring_id"]
    await mediator.handle(
        DeactivateRecurringBookingRequest(recurring_booking_id=recurring_id)
    )
    await callback.answer("Постоянная запись остановлена")
    await dialog_manager.switch_to(TrainerRecurringSG.list)


async def on_edit_recurring_date_clicked(
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
    dialog_manager.dialog_data["new_recurring_day"] = clicked_date.isoformat()
    await dialog_manager.switch_to(TrainerRecurringSG.edit_time)


async def on_edit_recurring_time_clicked(
    callback: CallbackQuery,
    widget: Select[str],
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["new_recurring_slot_id"] = int(item_id)
    await dialog_manager.switch_to(TrainerRecurringSG.edit_confirm)


@inject
async def on_edit_recurring_confirm(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    recurring_id: int = dialog_manager.dialog_data["editing_recurring_id"]
    new_slot_id: int = dialog_manager.dialog_data["new_recurring_slot_id"]

    try:
        await mediator.handle(
            ChangeRecurringBookingScheduleRequest(
                recurring_booking_id=recurring_id,
                new_slot_id=new_slot_id,
            )
        )
    except SlotFullException:
        await callback.answer("Мест не осталось на этом слоте", show_alert=True)
        return

    await callback.answer("Расписание обновлено!", show_alert=True)
    await dialog_manager.switch_to(TrainerRecurringSG.list)
