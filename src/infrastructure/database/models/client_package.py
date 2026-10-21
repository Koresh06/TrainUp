from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    VARCHAR,
    Boolean,
    Date,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.entities.client_package import ClientPackage
from src.domain.enums.package import PackageStatus

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin


class ClientPackageModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "client_packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="CASCADE"), index=True
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(VARCHAR(100))
    sessions_total: Mapped[int] = mapped_column(Integer)
    sessions_used: Mapped[int] = mapped_column(Integer, default=0)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[PackageStatus] = mapped_column(SqlEnum(PackageStatus, name="packagestatus"))
    is_bonus: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    @classmethod
    def from_entity(cls, entity: ClientPackage) -> "ClientPackageModel":
        model = cls()
        model.update_model(entity)
        return model

    def to_entity(self) -> ClientPackage:
        return ClientPackage(
            id=self.id,
            trainer_id=self.trainer_id,
            client_id=self.client_id,
            title=self.title,
            sessions_total=self.sessions_total,
            sessions_used=self.sessions_used,
            price=self.price,
            paid_at=self.paid_at,
            valid_until=self.valid_until,
            status=self.status,
            is_bonus=self.is_bonus,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def update_model(self, entity: ClientPackage) -> None:
        self.trainer_id = entity.trainer_id
        self.client_id = entity.client_id
        self.title = entity.title
        self.sessions_total = entity.sessions_total
        self.sessions_used = entity.sessions_used
        self.price = entity.price
        self.paid_at = entity.paid_at
        self.valid_until = entity.valid_until
        self.status = entity.status
        self.is_bonus = entity.is_bonus
