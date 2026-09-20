from datetime import date

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.booking.count_active_by_slot_ids import (
    CountActiveBookingsBySlotIdsRequest,
)
from src.application.use_cases.calendar.get_day_availability_map_assignment import (
    GetDayAvailabilityMapForAssignmentRequest,
)
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsRequest
from src.application.use_cases.calendar.get_slot_by_id import GetSlotByIdRequest
from src.application.use_cases.client.get_by_id import GetClientByIdRequest
from src.application.use_cases.client.get_clients_by_trainer import (
    GetClientsByTrainerIdRequest,
)
from src.application.use_cases.recurring_booking.get_all_active_by_trainer import (
    GetActiveRecurringBookingsByTrainerRequest,
)
from src.application.use_cases.recurring_booking.get_by_id import (
    GetRecurringBookingByIdRequest,
)
from src.application.use_cases.trainer_booking_settings.get_by_id import (
    GetTrainerBookingSettingsRequest,
)
from src.application.use_cases.recurring_booking.get_active_by_client import (
    GetActiveRecurringBookingsByClientRequest,
)
from src.domain.constants import WEEKDAY_LABELS_FULL
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.client import Client
from src.domain.entities.recurring_booking import RecurringBooking
from src.domain.entities.trainer_booking_settings import TrainerBookingSettings
from src.domain.enums.slot import SlotStatus
from src.presentation.telegram.widgets.booking_calendar import (
    AVAILABILITY_CACHE_KEY,
    HORIZON_CACHE_KEY,
)


@inject
async def recurring_clients_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    recurring_list: list[RecurringBooking] = await mediator.handle(
        GetActiveRecurringBookingsByTrainerRequest(trainer_id=trainer_id)
    )

    by_client: dict[int, list[RecurringBooking]] = {}
    for r in recurring_list:
        by_client.setdefault(r.client_id, []).append(r)

    items = []
    for client_id, bookings in by_client.items():
        client: Client = await mediator.handle(
            GetClientByIdRequest(client_id=client_id)
        )
        name = f"{client.first_name} {client.last_name or ''}".strip()
        items.append({"id": str(client_id), "label": f"{name} ({len(bookings)})"})

    items.sort(key=lambda i: i["label"])
    return {"recurring_list": items}


@inject
async def select_client_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    clients: list[Client] = await mediator.handle(
        GetClientsByTrainerIdRequest(trainer_id=trainer_id)
    )
    return {
        "clients": [
            {
                "id": str(c.id),
                "label": f"{c.first_name} {c.last_name or ''}".strip(),
            }
            for c in clients
        ]
    }


@inject
async def recurring_client_bookings_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    client_id: int = dialog_manager.dialog_data["selected_client_id"]

    client_recurring: list[RecurringBooking] = await mediator.handle(
        GetActiveRecurringBookingsByClientRequest(
            trainer_id=trainer_id, client_id=client_id
        )
    )
    client: Client = await mediator.handle(GetClientByIdRequest(client_id=client_id))

    items = []
    for r in sorted(client_recurring, key=lambda r: (r.weekday, r.start_time)):
        weekday_label = WEEKDAY_LABELS_FULL[r.weekday]
        items.append(
            {
                "id": str(r.id),
                "label": f"{weekday_label} — {r.start_time.strftime('%H:%M')}",
            }
        )

    return {
        "client_name": f"{client.first_name} {client.last_name or ''}".strip(),
        "recurring_list": items,
    }


@inject
async def recurring_day_calendar_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]

    settings: TrainerBookingSettings = await mediator.handle(
        GetTrainerBookingSettingsRequest(trainer_id=trainer_id)
    )

    availability_map: dict[date, int] = await mediator.handle(
        GetDayAvailabilityMapForAssignmentRequest(
            trainer_id=trainer_id,
            days_ahead=settings.calendar_horizon_days,
        )
    )

    dialog_manager.dialog_data[AVAILABILITY_CACHE_KEY] = {
        d.isoformat(): count for d, count in availability_map.items()
    }
    dialog_manager.dialog_data[HORIZON_CACHE_KEY] = settings.calendar_horizon_days

    return {}


@inject
async def recurring_times_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    selected_day = date.fromisoformat(dialog_manager.dialog_data["selected_day"])

    slots: list[CalendarSlot] = await mediator.handle(
        GetDaySlotsRequest(trainer_id=trainer_id, slot_date=selected_day)
    )
    slots = [s for s in slots if s.status != SlotStatus.BLOCKED]
    slots.sort(key=lambda s: s.start_time)

    slot_ids = [s.id for s in slots]
    booked_counts = await mediator.handle(
        CountActiveBookingsBySlotIdsRequest(slot_ids=slot_ids)
    )

    times = []
    for slot in slots:
        occupied = booked_counts.get(slot.id, 0)
        label = f"{slot.start_time.strftime('%H:%M')} ({occupied}/{slot.capacity})"
        times.append({"value_id": str(slot.id), "label": label})

    return {
        "times": times,
        "selected_day_label": selected_day.strftime("%d.%m.%Y"),
    }


@inject
async def recurring_confirm_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    slot_id: int = dialog_manager.dialog_data["selected_slot_id"]
    client_id: int = dialog_manager.dialog_data["selected_client_id"]

    slot: CalendarSlot = await mediator.handle(GetSlotByIdRequest(slot_id=slot_id))
    client: Client = await mediator.handle(GetClientByIdRequest(client_id=client_id))

    weekday_label = WEEKDAY_LABELS_FULL[slot.slot_date.weekday()]

    return {
        "client_name": f"{client.first_name} {client.last_name or ''}".strip(),
        "date": slot.slot_date.strftime("%d.%m.%Y"),
        "time": slot.start_time.strftime("%H:%M"),
        "weekday_label": weekday_label,
    }


@inject
async def recurring_detail_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    recurring_id: int = dialog_manager.dialog_data["editing_recurring_id"]
    recurring: RecurringBooking = await mediator.handle(
        GetRecurringBookingByIdRequest(recurring_booking_id=recurring_id)
    )
    client: Client = await mediator.handle(
        GetClientByIdRequest(client_id=recurring.client_id)
    )

    return {
        "client_name": f"{client.first_name} {client.last_name or ''}".strip(),
        "weekday_label": WEEKDAY_LABELS_FULL[recurring.weekday],
        "time": recurring.start_time.strftime("%H:%M"),
    }


@inject
async def edit_recurring_day_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    settings: TrainerBookingSettings = await mediator.handle(
        GetTrainerBookingSettingsRequest(trainer_id=trainer_id)
    )
    availability_map: dict[date, int] = await mediator.handle(
        GetDayAvailabilityMapForAssignmentRequest(
            trainer_id=trainer_id, days_ahead=settings.calendar_horizon_days
        )
    )
    dialog_manager.dialog_data[AVAILABILITY_CACHE_KEY] = {
        d.isoformat(): count for d, count in availability_map.items()
    }
    dialog_manager.dialog_data[HORIZON_CACHE_KEY] = settings.calendar_horizon_days
    return {}


@inject
async def edit_recurring_times_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    selected_day = date.fromisoformat(dialog_manager.dialog_data["new_recurring_day"])

    slots: list[CalendarSlot] = await mediator.handle(
        GetDaySlotsRequest(trainer_id=trainer_id, slot_date=selected_day)
    )
    slots = [s for s in slots if s.status != SlotStatus.BLOCKED]
    slots.sort(key=lambda s: s.start_time)

    slot_ids = [s.id for s in slots]
    booked_counts = await mediator.handle(
        CountActiveBookingsBySlotIdsRequest(slot_ids=slot_ids)
    )

    times = []
    for slot in slots:
        occupied = booked_counts.get(slot.id, 0)
        label = (
            f"{slot.start_time.strftime('%H:%M')} (занято {occupied}/{slot.capacity})"
        )
        times.append({"value_id": str(slot.id), "label": label})

    return {"times": times, "selected_day_label": selected_day.strftime("%d.%m.%Y")}


@inject
async def edit_recurring_confirm_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    slot_id: int = dialog_manager.dialog_data["new_recurring_slot_id"]
    slot: CalendarSlot = await mediator.handle(GetSlotByIdRequest(slot_id=slot_id))
    weekday_label = WEEKDAY_LABELS_FULL[slot.slot_date.weekday()]
    return {
        "date": slot.slot_date.strftime("%d.%m.%Y"),
        "time": slot.start_time.strftime("%H:%M"),
        "weekday_label": weekday_label,
    }
