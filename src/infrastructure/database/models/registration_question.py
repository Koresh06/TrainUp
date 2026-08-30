from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    ARRAY,
    ForeignKey,
    Integer,
    VARCHAR,
    Boolean,
    Enum as SqlEnum,
    String,
)

from src.domain.entities.registration_question import RegistrationQuestion
from src.domain.enums.question_type import QuestionType

from .base import BaseModel, CreatedAtMixin, UpdatedAtMixin


class RegistrationQuestionModel(BaseModel, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "registration_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("trainers.id", ondelete="CASCADE"), index=True
    )
    question_type: Mapped[QuestionType] = mapped_column(
        SqlEnum(QuestionType, name="question_type", create_type=True)
    )
    label: Mapped[str] = mapped_column(String(500))
    options: Mapped[list[str]] = mapped_column(ARRAY(VARCHAR(255)), default=list)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    system_key: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    @classmethod
    def from_entity(cls, entity: "RegistrationQuestion") -> "RegistrationQuestionModel":
        return cls(
            trainer_id=entity.trainer_id,
            question_type=entity.question_type,
            label=entity.label,
            options=entity.options,
            is_required=entity.is_required,
            order=entity.order,
            is_system=entity.is_system,
            system_key=entity.system_key,
            is_active=entity.is_active,
        )

    def to_entity(self) -> "RegistrationQuestion":
        return RegistrationQuestion(
            id=self.id,
            trainer_id=self.trainer_id,
            question_type=self.question_type,
            label=self.label,
            options=self.options or [],
            is_required=self.is_required,
            order=self.order,
            is_system=self.is_system,
            system_key=self.system_key,
            is_active=self.is_active,
        )

    def update_model(self, entity: "RegistrationQuestion") -> None:
        self.trainer_id = entity.trainer_id
        self.question_type = entity.question_type
        self.label = entity.label
        self.options = entity.options
        self.is_required = entity.is_required
        self.order = entity.order
        self.is_system = entity.is_system
        self.system_key = entity.system_key
        self.is_active = entity.is_active
