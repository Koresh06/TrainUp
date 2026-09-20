from datetime import date

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.use_cases.booking.count_active_by_slot_ids import (
    CountActiveBookingsBySlotIdsRequest,
)
from src.application.use_cases.calendar.get_day_availability_map import (
    GetDayAvailabilityMapRequest,
)
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsRequest
from src.application.use_cases.calendar.get_slot_by_id import GetSlotByIdRequest
from src.application.use_cases.client.get_by_id import GetClientByIdRequest
from src.application.use_cases.trainer_booking_settings.get_by_id import (
    GetTrainerBookingSettingsRequest,
)
from src.domain.entities.booking import Booking
from src.application.mediator import Mediator
from src.application.use_cases.trainer.get_upcoming_bookings_by_trainer import (
    GetUpcomingBookingsByTrainerRequest,
)
from src.application.use_cases.booking.get_history_by_trainer import (
    GetBookingsHistoryByTrainerRequest,
)
from src.application.use_cases.booking.get_by_id import GetBookingByIdRequest
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.client import Client
from src.domain.entities.trainer_booking_settings import TrainerBookingSettings
from src.domain.enums.booking import BookingStatus, BookingsListMode
from src.domain.enums.slot import SlotStatus
from src.presentation.telegram.widgets.booking_calendar import (
    AVAILABILITY_CACHE_KEY,
    HORIZON_CACHE_KEY,
)

BOOKING_STATUS_LABELS: dict[BookingStatus, str] = {
    BookingStatus.PENDING: "⏳",
    BookingStatus.CONFIRMED: "✅",
    BookingStatus.CANCELLED: "❌",
    BookingStatus.COMPLETED: "🏁",
}


@inject
async def bookings_list_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    mode = dialog_manager.dialog_data.get(
        "bookings_mode", BookingsListMode.UPCOMING.value
    )
    is_history = mode == BookingsListMode.HISTORY.value

    if is_history:
        bookings: list[Booking] = await mediator.handle(
            GetBookingsHistoryByTrainerRequest(trainer_id=trainer_id)
        )
        title = "🕓 <b>История</b>"
    else:
        bookings = await mediator.handle(
            GetUpcomingBookingsByTrainerRequest(trainer_id=trainer_id)
        )
        title = "📅 <b>Текущие</b>"

    items = []
    for b in bookings:
        slot: CalendarSlot = await mediator.handle(GetSlotByIdRequest(slot_id=b.slot_id))
        client: Client = await mediator.handle(GetClientByIdRequest(client_id=b.client_id))

        client_short = client.first_name
        if client.last_name:
            client_short += f" {client.last_name[0]}."

        label = (
            f"{BOOKING_STATUS_LABELS.get(b.status, '')} "
            f"{'🔁 ' if b.recurring_booking_id is not None else ''}"
            f"{slot.slot_date.strftime('%d.%m')} {slot.start_time.strftime('%H:%M')} — "
            f"{client_short}"
        )
        items.append({"id": str(b.id), "label": label})

    return {
        "bookings": items,
        "title": title,
        "is_upcoming": not is_history,
        "is_history": is_history,
        "empty_hint": "\n\nЗаписей пока нет" if not items else "",
    }


@inject
async def booking_detail_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    booking_id: int = dialog_manager.dialog_data["editing_booking_id"]
    mode = dialog_manager.dialog_data.get(
        "bookings_mode", BookingsListMode.UPCOMING.value
    )
    is_history = mode == BookingsListMode.HISTORY.value

    booking: Booking = await mediator.handle(
        GetBookingByIdRequest(booking_id=booking_id)
    )
    slot: CalendarSlot = await mediator.handle(
        GetSlotByIdRequest(slot_id=booking.slot_id)
    )
    client: Client = await mediator.handle(
        GetClientByIdRequest(client_id=booking.client_id)
    )

    client_name = f"{client.first_name} {client.last_name or ''}".strip()

    contact_lines = [f'💬 <a href="tg://user?id={client.tg_id}">Написать клиенту в Telegram</a>']
    if client.username:
        contact_lines.append(f"👤 @{client.username}")
    contact_lines.append(f"📞 {client.phone}")
    contact_block = "\n".join(contact_lines)

    return {
        "client_name": client_name,
        "contact_block": contact_block,
        "date": slot.slot_date.strftime("%d.%m.%Y"),
        "time": slot.start_time.strftime("%H:%M"),
        "status": BOOKING_STATUS_LABELS.get(booking.status, booking.status.name),
        "is_recurring": booking.recurring_booking_id is not None,
        "recurring_note": (
            "\n🔁 <b>Постоянная тренировка</b>"
            if booking.recurring_booking_id is not None
            else ""
        ),
        "is_history": is_history,
        "is_upcoming": not is_history,
    }


@inject
async def reschedule_day_calendar_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    settings: TrainerBookingSettings = await mediator.handle(
        GetTrainerBookingSettingsRequest(trainer_id=trainer_id)
    )
    availability_map: dict[date, int] = await mediator.handle(
        GetDayAvailabilityMapRequest(
            trainer_id=trainer_id, days_ahead=settings.calendar_horizon_days
        )
    )
    dialog_manager.dialog_data[AVAILABILITY_CACHE_KEY] = {
        d.isoformat(): count for d, count in availability_map.items()
    }
    dialog_manager.dialog_data[HORIZON_CACHE_KEY] = settings.calendar_horizon_days
    return {}


@inject
async def reschedule_times_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    selected_day = date.fromisoformat(dialog_manager.dialog_data["reschedule_day"])

    slots: list[CalendarSlot] = await mediator.handle(
        GetDaySlotsRequest(trainer_id=trainer_id, slot_date=selected_day)
    )
    slots.sort(key=lambda s: s.start_time)

    slot_ids = [s.id for s in slots]
    booked_counts = await mediator.handle(
        CountActiveBookingsBySlotIdsRequest(slot_ids=slot_ids)
    )

    times = []
    for slot in slots:
        free_spots = slot.capacity - booked_counts.get(slot.id, 0)
        is_free = slot.status != SlotStatus.BLOCKED and free_spots > 0
        if not is_free:
            continue
        label = f"{slot.start_time.strftime('%H:%M')}" + (
            f" ({free_spots})" if slot.capacity > 1 else ""
        )
        times.append({"value_id": str(slot.id), "label": label})

    return {"times": times, "selected_day_label": selected_day.strftime("%d.%m.%Y")}


@inject
async def reschedule_confirm_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    new_slot_id: int = dialog_manager.dialog_data["new_slot_id"]
    slot: CalendarSlot = await mediator.handle(GetSlotByIdRequest(slot_id=new_slot_id))
    return {
        "date": slot.slot_date.strftime("%d.%m.%Y"),
        "time": slot.start_time.strftime("%H:%M"),
    }
