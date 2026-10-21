from datetime import date

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram.types import CallbackQuery
from aiogram_dialog import ChatEvent, DialogManager
from aiogram_dialog.widgets.kbd import Button, ManagedCalendar, Select

from src.application.mediator import Mediator
from src.application.use_cases.booking.count_active_by_slot_ids import (
    CountActiveBookingsBySlotIdsRequest,
)
from src.application.use_cases.calendar.get_slot_by_id import GetSlotByIdRequest
from src.application.use_cases.calendar.set_day_blocked import SetDayBlockedRequest
from src.application.use_cases.calendar.set_slot_blocked import SetSlotBlockedRequest
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.enums.slot import SlotStatus

from src.presentation.telegram.features.trainer.vacation.states import TrainerVacationSG

from .getters import DAYS_WITH_SLOTS_CACHE_KEY
from .states import TrainerBlockingSG

BOOKINGS_KEPT_HINT = (
    "Существующие записи сохранены — при необходимости отмените или перенесите "
    "их в «📅 Расписании»."
)


async def on_blocking_date_clicked(
    callback: ChatEvent,
    widget: ManagedCalendar,
    dialog_manager: DialogManager,
    clicked_date: date,
    **kwargs,
) -> None:
    days_with_slots: list[str] = dialog_manager.dialog_data.get(
        DAYS_WITH_SLOTS_CACHE_KEY, []
    )
    if clicked_date.isoformat() not in days_with_slots:
        await callback.answer("На этот день нет слотов в расписании", show_alert=True)
        return

    dialog_manager.dialog_data["blocking_day"] = clicked_date.isoformat()
    await dialog_manager.switch_to(TrainerBlockingSG.day)


@inject
async def on_blocking_slot_clicked(
    callback: CallbackQuery,
    widget: Select[str],
    dialog_manager: DialogManager,
    item_id: str,
    mediator: FromDishka[Mediator],
) -> None:
    slot: CalendarSlot = await mediator.handle(GetSlotByIdRequest(slot_id=int(item_id)))
    block = slot.status != SlotStatus.BLOCKED
    await mediator.handle(SetSlotBlockedRequest(slot_id=slot.id, blocked=block))

    if not block:
        await callback.answer("✅ Слот снова открыт для записи")
        return

    booked: dict[int, int] = await mediator.handle(
        CountActiveBookingsBySlotIdsRequest(slot_ids=[slot.id])
    )
    if booked.get(slot.id, 0):
        await callback.answer(
            f"🚫 Слот закрыт для новых записей. {BOOKINGS_KEPT_HINT}", show_alert=True
        )
    else:
        await callback.answer("🚫 Слот закрыт для записи")


@inject
async def on_block_day_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    block = button.widget_id == "block_day"
    changed: int = await mediator.handle(
        SetDayBlockedRequest(
            trainer_id=dialog_manager.start_data["trainer_id"],
            slot_date=date.fromisoformat(dialog_manager.dialog_data["blocking_day"]),
            blocked=block,
        )
    )
    if not changed:
        await callback.answer("Ничего не изменилось")
    elif block:
        await callback.answer(f"🚫 День закрыт для записи. {BOOKINGS_KEPT_HINT}", show_alert=True)
    else:
        await callback.answer("✅ День снова открыт для записи")


async def on_open_vacation(
    callback: CallbackQuery, button: Button, dialog_manager: DialogManager
) -> None:
    await dialog_manager.start(
        state=TrainerVacationSG.list,
        data={"trainer_id": dialog_manager.start_data["trainer_id"]},
    )
