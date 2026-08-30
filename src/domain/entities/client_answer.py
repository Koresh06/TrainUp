from dataclasses import dataclass

from src.domain.entities.base import Entity


@dataclass(kw_only=True)
class ClientAnswer(Entity):
    client_id: int
    question_id: int
    value: list[str]   # TEXT — [строка]; MULTI_SELECT — выбранные варианты