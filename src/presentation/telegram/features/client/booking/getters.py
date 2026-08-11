from datetime import date
from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager


from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.enums.slot import SlotStatus
from src.application.mediator import Mediator
from src.application.use_cases.calendar.get_day_availability_map import (
    GetDayAvailabilityMapRequest,
)
from src.application.use_cases.calendar.get_slot_by_id import GetSlotByIdRequest
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsRequest

ROLLING_DAYS_AHEAD = 60
AVAILABILITY_CACHE_KEY = "day_availability"


@inject
async def day_calendar_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]

    availability_map: dict[date, int] = await mediator.handle(
        GetDayAvailabilityMapRequest(
            trainer_id=trainer_id, days_ahead=ROLLING_DAYS_AHEAD
        )
    )

    dialog_manager.dialog_data[AVAILABILITY_CACHE_KEY] = {
        d.isoformat(): count for d, count in availability_map.items()
    }
    return {}


@inject
async def times_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    selected_day = date.fromisoformat(dialog_manager.dialog_data["selected_day"])

    slots: list[CalendarSlot] = await mediator.handle(
        GetDaySlotsRequest(trainer_id=trainer_id, slot_date=selected_day)
    )
    slots.sort(key=lambda s: s.start_time)

    times = []
    cache: dict[str, str] = {}
    for slot in slots:
        is_free = slot.status == SlotStatus.FREE
        kind = "free" if is_free else "locked"
        times.append(
            {
                "value_id": str(slot.id),
                "label": slot.start_time.strftime("%H:%M"),
                "kind": kind,
            }
        )
        cache[str(slot.id)] = kind

    dialog_manager.dialog_data["time_kind_cache"] = cache

    return {
        "times": times,
        "selected_day_label": selected_day.strftime("%d.%m.%Y"),
    }


@inject
async def confirm_booking_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    slot_id: int = dialog_manager.dialog_data["selected_slot_id"]
    slot: CalendarSlot = await mediator.handle(GetSlotByIdRequest(slot_id=slot_id))

    return {
        "date": slot.slot_date.strftime("%d.%m.%Y"),
        "time": slot.start_time.strftime("%H:%M"),
    }
