from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    ForeignKey,
    Integer,
    VARCHAR,
    Enum as SqlEnum,
)

from src.domain.entities.consultation import ConsultationRequest
from src.domain.enums.request import RequestStatus
from src.domain.enums.consultation import ConsultationType

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models import ClientModel, TrainerModel


class ConsultationRequestModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "consultation_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        index=True,
    )
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="CASCADE"),
        index=True,
    )
    consultation_type: Mapped[ConsultationType] = mapped_column(SqlEnum(ConsultationType))
    comment: Mapped[str | None] = mapped_column(VARCHAR(255))
    status: Mapped[RequestStatus] = mapped_column(
        SqlEnum(RequestStatus),
        default=RequestStatus.NEW,
    )

    client: Mapped["ClientModel"] = relationship("ClientModel")
    trainer: Mapped["TrainerModel"] = relationship("TrainerModel")

    @classmethod
    def from_entity(cls, entity: ConsultationRequest) -> "ConsultationRequestModel":
        return cls(
            client_id=entity.client_id,
            trainer_id=entity.trainer_id,
            consultation_type=entity.consultation_type,
            comment=entity.comment,
            status=entity.status,
        )

    def to_entity(self) -> ConsultationRequest:
        return ConsultationRequest(
            id=self.id,
            client_id=self.client_id,
            trainer_id=self.trainer_id,
            consultation_type=self.consultation_type,
            comment=self.comment,
            status=self.status,
        )

    def update_model(self, entity: ConsultationRequest) -> None:
        self.client_id = entity.client_id
        self.trainer_id = entity.trainer_id
        self.consultation_type = entity.consultation_type
        self.comment = entity.comment
        self.status = entity.status
