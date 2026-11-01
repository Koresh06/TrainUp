from sqlalchemy import ARRAY, VARCHAR, BigInteger, Integer, text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.entities.bot_admin import BotAdmin
from src.domain.enums.admin import AdminNotification, AdminPermission

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin


class BotAdminModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "bot_admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    permissions: Mapped[list[str]] = mapped_column(
        ARRAY(VARCHAR(32)), server_default=text("'{}'")
    )
    muted_notifications: Mapped[list[str]] = mapped_column(
        ARRAY(VARCHAR(32)), server_default=text("'{}'")
    )
    added_by_tg_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    @classmethod
    def from_entity(cls, entity: BotAdmin) -> "BotAdminModel":
        model = cls(tg_id=entity.tg_id, added_by_tg_id=entity.added_by_tg_id)
        model.update_model(entity)
        return model

    def to_entity(self) -> BotAdmin:
        return BotAdmin(
            id=self.id,
            tg_id=self.tg_id,
            name=self.name,
            permissions={AdminPermission(value) for value in self.permissions},
            muted_notifications={
                AdminNotification(value) for value in self.muted_notifications
            },
            added_by_tg_id=self.added_by_tg_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def update_model(self, entity: BotAdmin) -> None:
        self.name = entity.name
        self.permissions = sorted(p.value for p in entity.permissions)
        self.muted_notifications = sorted(n.value for n in entity.muted_notifications)
