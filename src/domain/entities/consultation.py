from dataclasses import dataclass

from src.domain.entities.base import Entity
from src.domain.enums.consultation import ConsultationType
from src.domain.enums.request import RequestStatus


@dataclass(kw_only=True)
class ConsultationRequest(Entity):
    client_id: int
    trainer_id: int
    consultation_type: ConsultationType
    comment: str | None = None
    status: RequestStatus = RequestStatus.NEW
