from dataclasses import dataclass
from datetime import time

from src.domain.entities.base import Entity


@dataclass(kw_only=True)
class RecurringBooking(Entity):
    trainer_id: int
    client_id: int
    weekday: int
    start_time: time
    is_active: bool = True