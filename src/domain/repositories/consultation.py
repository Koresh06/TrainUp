from typing import Protocol

from src.domain.entities.consultation import ConsultationRequest


class ConsultationRequestRepository(Protocol):
    async def get_by_id(self, consultation_id: int) -> ConsultationRequest | None:
        ...

    async def save(self, consultation: ConsultationRequest) -> ConsultationRequest:
        ...