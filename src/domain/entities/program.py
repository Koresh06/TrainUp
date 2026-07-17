from dataclasses import dataclass

from src.domain.entities.base import Entity
from src.domain.enums.program import ProgramType
from src.domain.enums.request import RequestStatus
from src.domain.enums.training import TrainingDirection


@dataclass(kw_only=True)
class ProgramRequest(Entity):
    client_id: int
    trainer_id: int
    program_type: ProgramType
    direction: TrainingDirection
    comment: str | None = None
    status: RequestStatus = RequestStatus.NEW
