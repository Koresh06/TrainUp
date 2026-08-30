from dataclasses import dataclass

from src.domain.exception.base import DomainError


@dataclass
class RegistrationQuestionNotFoundException(DomainError):
    registration_question_id: str

    @property
    def message(self) -> str:
        return f"Регистрационный вопрос с id {self.registration_question_id} не найден"


@dataclass
class CannotDeleteSystemQuestionError(DomainError):
    registration_question_id: str

    @property
    def message(self) -> str:
        return f"Нельзя удалить системное регистрационное вопрос с id {self.registration_question_id}"