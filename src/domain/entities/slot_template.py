from dataclasses import dataclass
from datetime import time

from src.domain.entities.base import Entity


@dataclass(kw_only=True)
class SlotTemplate(Entity):
    trainer_id: int
    weekday: int
    start_time: time
    end_time: time
    capacity: int = 1
    is_active: bool = True