from datetime import date

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.booking.count_active_by_slot_ids import (
    CountActiveBookingsBySlotIdsRequest,
)
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsRequest
from src.application.use_cases.calendar.get_week_grid import GetWeekGridRequest
from src.application.use_cases.trainer_booking_settings.get_by_id import (
    GetTrainerBookingSettingsRequest,
)
from src.domain.constants import WEEKDAY_LABELS_FULL
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.trainer_booking_settings import TrainerBookingSettings
from src.domain.enums.slot import SlotStatus
from src.domain.utils import is_slot_in_past
from src.presentation.telegram.widgets.booking_calendar import (
    AVAILABILITY_CACHE_KEY,
    HORIZON_CACHE_KEY,
)

DAYS_WITH_SLOTS_CACHE_KEY = "days_with_slots"


@inject
async def blocking_calendar_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    settings: TrainerBookingSettings = await mediator.handle(
        GetTrainerBookingSettingsRequest(trainer_id=trainer_id)
    )
    slots: list[CalendarSlot] = await mediator.handle(
        GetWeekGridRequest(trainer_id=trainer_id, days_ahead=settings.calendar_horizon_days)
    )
    slots = [s for s in slots if not is_slot_in_past(s)]

    # зелёный день — есть незаблокированные слоты, красный — всё закрыто;
    # кликабельны все дни, где вообще есть слоты (чтобы можно было разблокировать)
    open_counts: dict[str, int] = {}
    days_with_slots: set[str] = set()
    for slot in slots:
        key = slot.slot_date.isoformat()
        days_with_slots.add(key)
        if slot.status != SlotStatus.BLOCKED:
            open_counts[key] = open_counts.get(key, 0) + 1

    dialog_manager.dialog_data[AVAILABILITY_CACHE_KEY] = open_counts
    dialog_manager.dialog_data[DAYS_WITH_SLOTS_CACHE_KEY] = sorted(days_with_slots)
    dialog_manager.dialog_data[HORIZON_CACHE_KEY] = settings.calendar_horizon_days
    return {}


@inject
async def blocking_day_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    selected_day = date.fromisoformat(dialog_manager.dialog_data["blocking_day"])

    slots: list[CalendarSlot] = await mediator.handle(
        GetDaySlotsRequest(trainer_id=trainer_id, slot_date=selected_day)
    )
    slots = [s for s in slots if not is_slot_in_past(s)]
    slots.sort(key=lambda s: s.start_time)
    booked_counts: dict[int, int] = await mediator.handle(
        CountActiveBookingsBySlotIdsRequest(slot_ids=[s.id for s in slots])
    )

    times = []
    for slot in slots:
        is_blocked = slot.status == SlotStatus.BLOCKED
        booked = booked_counts.get(slot.id, 0)
        times.append(
            {
                "value_id": str(slot.id),
                "label": (
                    f"{'🚫' if is_blocked else '🟢'} "
                    f"{slot.start_time.strftime('%H:%M')} ({booked}/{slot.capacity})"
                ),
                "kind": "locked" if is_blocked else "free",
            }
        )

    return {
        "times": times,
        "day_label": (
            f"{selected_day.strftime('%d.%m.%Y')} "
            f"({WEEKDAY_LABELS_FULL[selected_day.weekday()].lower()})"
        ),
        "has_slots": bool(times),
    }
