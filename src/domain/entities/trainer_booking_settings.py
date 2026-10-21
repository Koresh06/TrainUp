from dataclasses import dataclass

from src.domain.entities.base import Entity


@dataclass(kw_only=True)
class TrainerBookingSettings(Entity):
    trainer_id: int
    calendar_horizon_days: int
    max_active_bookings_per_client: int
    # неявка списывает занятие с абонемента (как и проведённая тренировка)
    no_show_charges_package: bool = True
    # накануне спрашивать клиента «придёте?» (✅ приду / ❌ не смогу)
    ask_attendance_confirmation: bool = True
    # после тренировки просить клиента оценить её (1–5 ⭐)
    ask_rating: bool = True