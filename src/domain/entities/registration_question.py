from dataclasses import dataclass, field

from src.domain.entities.base import Entity
from src.domain.enums.question_type import QuestionType


@dataclass(kw_only=True)
class RegistrationQuestion(Entity):
    trainer_id: int
    question_type: QuestionType
    label: str
    options: list[str] = field(default_factory=list)   # только для MULTI_SELECT
    is_required: bool = True
    order: int = 0
    is_system: bool = False   # True для health_conditions/goals — нельзя удалить, можно править варианты
    system_key: str | None = None  # "health_conditions" | "goals" | None
    is_active: bool = True