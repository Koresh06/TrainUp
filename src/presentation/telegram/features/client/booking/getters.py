from datetime import date
import logging
from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager


from src.application.use_cases.trainer_pricing_rule.get_by_id import GetTrainerPricingRuleRequest
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.trainer_booking_settings import TrainerBookingSettings
from src.domain.entities.trainer_pricing_rule import TrainerPricingRule
from src.domain.enums.slot import SlotStatus
from src.application.mediator import Mediator
from src.application.use_cases.calendar.get_day_availability_map import (
    GetDayAvailabilityMapRequest,
)
from src.application.use_cases.trainer_booking_settings.get_by_id import (
    GetTrainerBookingSettingsRequest,
)
from src.application.use_cases.booking.count_active_by_slot_ids import (
    CountActiveBookingsBySlotIdsRequest,
)
from src.application.use_cases.calendar.get_slot_by_id import GetSlotByIdRequest
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsRequest
from src.presentation.telegram.widgets.booking_calendar import AVAILABILITY_CACHE_KEY, HORIZON_CACHE_KEY


logger = logging.getLogger(__name__)


@inject
async def day_calendar_getter(
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
    logger.info("[DEBUG] times_getter slots=%s selected_day=%s", len(slots), selected_day)
    slots.sort(key=lambda s: s.start_time)

    slot_ids = [s.id for s in slots]
    booked_counts = await mediator.handle(
        CountActiveBookingsBySlotIdsRequest(slot_ids=slot_ids)
    )

    times = []
    cache: dict[str, str] = {}
    for slot in slots:
        free_spots = slot.capacity - booked_counts.get(slot.id, 0)
        is_blocked = slot.status == SlotStatus.BLOCKED
        is_free = not is_blocked and free_spots > 0

        if is_free and slot.capacity > 1:
            label = f"{slot.start_time.strftime('%H:%M')} ({free_spots})"
        else:
            label = slot.start_time.strftime("%H:%M")

        kind = "free" if is_free else "locked"
        times.append({"value_id": str(slot.id), "label": label, "kind": kind})
        cache[str(slot.id)] = kind

    dialog_manager.dialog_data["time_kind_cache"] = cache

    header_note = (
        "\n\nℹ️ Число в скобках — сколько мест ещё свободно."
        if any(s.capacity > 1 for s in slots)
        else ""
    )

    logger.info("[DEBUG] times_getter result times=%s", times)

    return {
        "times": times,
        "selected_day_label": selected_day.strftime("%d.%m.%Y"),
        "header_note": header_note,
    }

@inject
async def confirm_booking_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    slot_id: int = dialog_manager.dialog_data["selected_slot_id"]
    slot: CalendarSlot = await mediator.handle(GetSlotByIdRequest(slot_id=slot_id))

    pricing_rule: TrainerPricingRule | None = await mediator.handle(
        GetTrainerPricingRuleRequest(trainer_id=trainer_id)
    )
    price_label = ""
    if pricing_rule is not None:
        price = pricing_rule.price_for(slot.start_time)
        price_label = f"\n💰 Стоимость: {price:.0f} BYN"

    return {
        "date": slot.slot_date.strftime("%d.%m.%Y"),
        "time": slot.start_time.strftime("%H:%M"),
        "price_label": price_label,
    }