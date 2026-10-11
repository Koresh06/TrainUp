from datetime import datetime
from typing import Protocol

from src.domain.entities.consultation import ConsultationRequest
from src.domain.enums.request import RequestStatus


class ConsultationRequestRepository(Protocol):
    async def get_all(self) -> list[ConsultationRequest]:
        ...
        
    async def get_by_id(self, consultation_id: int) -> ConsultationRequest | None:
        ...

    async def save(self, consultation: ConsultationRequest) -> ConsultationRequest:
        ...

    async def get_by_trainer_id(
        self, trainer_id: int, statuses: list[RequestStatus]
    ) -> list[ConsultationRequest]:
        ...

    async def count_by_trainer_created_between(
        self, created_from: datetime, created_to: datetime
    ) -> dict[int, int]:
        ...
