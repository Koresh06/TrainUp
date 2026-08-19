from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    ForeignKey,
    BigInteger,
    Integer,
    VARCHAR,
    Boolean,
    String,
    Enum as SqlEnum,
)
from sqlalchemy.dialects.postgresql import ARRAY

from src.domain.entities.client import Client
from src.domain.enums.training import SportExperience

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models import (
        TrainerModel,
        BookingModel,
        ProgramRequestModel,
        FeedbackMessageModel,
    )


class ClientModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    first_name: Mapped[str] = mapped_column(VARCHAR(255))
    last_name: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    username: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    phone: Mapped[str] = mapped_column(VARCHAR(255))
    age: Mapped[int] = mapped_column(Integer)
    sport_experience: Mapped[SportExperience] = mapped_column(
        SqlEnum(
            SportExperience,
            name="sport_experience",
            create_type=True,
        ),
    )
    health_conditions: Mapped[list[str]] = mapped_column(ARRAY(VARCHAR(255)))
    health_conditions_other: Mapped[str | None] = mapped_column(
        String(1000), nullable=True
    )
    goals: Mapped[list[str]] = mapped_column(ARRAY(VARCHAR(255)))
    health_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    injuries: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    trainer: Mapped["TrainerModel"] = relationship(
        "TrainerModel",
        back_populates="clients",
    )
    bookings: Mapped[list["BookingModel"]] = relationship(
        "BookingModel",
        back_populates="client",
    )
    program_requests: Mapped[list["ProgramRequestModel"]] = relationship(
        "ProgramRequestModel",
        back_populates="client",
    )
    feedback_messages: Mapped[list["FeedbackMessageModel"]] = relationship(
        "FeedbackMessageModel",
        back_populates="client",
    )

    @classmethod
    def from_entity(cls, entity: "Client") -> "ClientModel":
        return cls(
            tg_id=entity.tg_id,
            trainer_id=entity.trainer_id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            username=entity.username,
            phone=entity.phone,
            age=entity.age,
            sport_experience=entity.sport_experience,
            health_conditions=entity.health_conditions,
            health_conditions_other=entity.health_conditions_other,
            goals=entity.goals,
            health_notes=entity.health_notes,
            injuries=entity.injuries,
            is_active=entity.is_active,
        )

    def to_entity(self) -> "Client":
        return Client(
            id=self.id,
            tg_id=self.tg_id,
            trainer_id=self.trainer_id,
            first_name=self.first_name,
            last_name=self.last_name,
            username=self.username,
            phone=self.phone,
            age=self.age,
            sport_experience=self.sport_experience,
            health_conditions=self.health_conditions,
            health_conditions_other=self.health_conditions_other,
            goals=self.goals,
            health_notes=self.health_notes,
            injuries=self.injuries,
            is_active=self.is_active,
        )

    def update_model(self, entity: "Client") -> None:
        self.tg_id = entity.tg_id
        self.trainer_id = entity.trainer_id
        self.first_name = entity.first_name
        self.last_name = entity.last_name
        self.username = entity.username
        self.phone = entity.phone
        self.age = entity.age
        self.sport_experience = entity.sport_experience
        self.health_conditions = entity.health_conditions
        self.health_conditions_other = entity.health_conditions_other
        self.goals = entity.goals
        self.health_notes = entity.health_notes
        self.injuries = entity.injuries
        self.is_active = entity.is_active
