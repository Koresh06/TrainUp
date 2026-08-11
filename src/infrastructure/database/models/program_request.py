from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    DateTime,
    ForeignKey,
    BigInteger,
    Integer,
    VARCHAR,
    Boolean,
    Enum as SqlEnum,
)

from src.domain.entities.program import ProgramRequest
from src.domain.enums.request import RequestStatus
from src.domain.enums.program import ProgramType
from src.domain.enums.training import TrainingDirection

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models import ClientModel, TrainerModel


class ProgramRequestModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "program_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        index=True,
    )
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="CASCADE"),
        index=True,
    )
    program_type: Mapped[ProgramType] = mapped_column(SqlEnum(ProgramType))
    direction: Mapped[TrainingDirection] = mapped_column(SqlEnum(TrainingDirection))
    comment: Mapped[str | None] = mapped_column(VARCHAR(255))
    status: Mapped[RequestStatus] = mapped_column(
        SqlEnum(RequestStatus),
        default=RequestStatus.NEW,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    client: Mapped["ClientModel"] = relationship(
        "ClientModel",
        back_populates="program_requests",
    )
    trainer: Mapped["TrainerModel"] = relationship(
        "TrainerModel",
        back_populates="program_requests",
    )

    @classmethod
    def from_entity(cls, entity: ProgramRequest) -> "ProgramRequestModel":
        return cls(
            client_id=entity.client_id,
            trainer_id=entity.trainer_id,
            program_type=entity.program_type,
            direction=entity.direction,
            comment=entity.comment,
            status=entity.status,
        )

    def to_entity(self):
        return ProgramRequest(
            id=self.id,
            client_id=self.client_id,
            trainer_id=self.trainer_id,
            program_type=self.program_type,
            direction=self.direction,
            comment=self.comment,
            status=self.status,
        )

    def update_model(self, entity: ProgramRequest) -> None:
        self.client_id = entity.client_id
        self.trainer_id = entity.trainer_id
        self.program_type = entity.program_type
        self.direction = entity.direction
        self.comment = entity.comment
        self.status = entity.status