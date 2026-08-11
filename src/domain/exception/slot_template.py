from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class SlotTemplateNotFoundException(DomainError):
    slot_template_id: int

    @property
    def message(self) -> str:
        return f"Шаблон слота с id {self.slot_template_id} не найден"
