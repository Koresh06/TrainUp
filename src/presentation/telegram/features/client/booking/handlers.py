from datetime import date

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery
from aiogram_dialog import ChatEvent, DialogManager
from aiogram_dialog.widgets.kbd.calendar_kbd import ManagedCalendar
from aiogram_dialog.widgets.kbd import Select, Button

from src.domain.entities.client import Client
from src.application.mediator import Mediator
from src.application.use_cases.client.get_by_tg_id import GetClientByTgIdRequest
from src.application.use_cases.booking.create import CreateBookingRequest
from src.presentation.telegram.features.client.booking.states import BookingSG


AVAILABILITY_CACHE_KEY = "day_availability"

async def on_date_clicked(
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

    dialog_manager.dialog_data["selected_day"] = clicked_date.isoformat()
    await dialog_manager.next()


async def on_time_clicked(
    callback: CallbackQuery,
    widget: Select[str],
    dialog_manager: DialogManager,
    item_id: str,
    /,
) -> None:
    kind = dialog_manager.dialog_data.get("time_kind_cache", {}).get(item_id)

    if kind != "free":
        await callback.answer("Слот занят или недоступен", show_alert=True)
        return

    dialog_manager.dialog_data["selected_slot_id"] = int(item_id)

    await dialog_manager.next()


@inject
async def on_confirm_booking(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> None:
    tg_id: int = callback.from_user.id
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    slot_id: int = dialog_manager.dialog_data["selected_slot_id"]

    client: Client = await mediator.handle(GetClientByTgIdRequest(tg_id=tg_id))

    await mediator.handle(
        CreateBookingRequest(
            client_id=client.id,
            trainer_id=trainer_id,
            slot_id=slot_id,
        )
    )

    await callback.answer()
    await callback.message.answer("Запись создана! Тренер подтвердит её в ближайшее время.")
    await dialog_manager.done()