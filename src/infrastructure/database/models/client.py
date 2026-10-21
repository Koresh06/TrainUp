from datetime import datetime
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

from src.domain.entities.client import Client
from src.domain.enums.client import ClientSource
from src.domain.enums.training import SportExperience

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models import (
        TrainerModel,
        BookingModel,
        ProgramRequestModel,
        FeedbackMessageModel,
        RecurringBookingModel,
    )


class ClientModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # NULL — клиент без Telegram (карточку завёл тренер); unique-индекс
    # в Postgres пропускает сколько угодно NULL
    tg_id: Mapped[int | None] = mapped_column(
        BigInteger, unique=True, index=True, nullable=True
    )
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    first_name: Mapped[str] = mapped_column(VARCHAR(255))
    last_name: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    username: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sport_experience: Mapped[SportExperience | None] = mapped_column(
        SqlEnum(
            SportExperience,
            name="sport_experience",
            create_type=True,
        ),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[ClientSource] = mapped_column(
        SqlEnum(ClientSource, name="clientsource"),
        default=ClientSource.TELEGRAM,
        server_default=ClientSource.TELEGRAM.name,
    )
    trainer_note: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
    invite_token: Mapped[str | None] = mapped_column(
        VARCHAR(64), unique=True, index=True, nullable=True
    )
    referral_code: Mapped[str | None] = mapped_column(
        VARCHAR(32), unique=True, index=True, nullable=True
    )
    referred_by_client_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True
    )
    referral_rewarded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

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
    recurring_bookings: Mapped[list["RecurringBookingModel"]] = relationship(
        "RecurringBookingModel",
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
            is_active=entity.is_active,
            source=entity.source,
            trainer_note=entity.trainer_note,
            invite_token=entity.invite_token,
            referral_code=entity.referral_code,
            referred_by_client_id=entity.referred_by_client_id,
            referral_rewarded_at=entity.referral_rewarded_at,
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
            is_active=self.is_active,
            source=self.source,
            trainer_note=self.trainer_note,
            invite_token=self.invite_token,
            referral_code=self.referral_code,
            referred_by_client_id=self.referred_by_client_id,
            referral_rewarded_at=self.referral_rewarded_at,
            created_at=self.created_at,
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
        self.is_active = entity.is_active
        self.source = entity.source
        self.trainer_note = entity.trainer_note
        self.invite_token = entity.invite_token
        self.referral_code = entity.referral_code
        self.referred_by_client_id = entity.referred_by_client_id
        self.referral_rewarded_at = entity.referral_rewarded_at
