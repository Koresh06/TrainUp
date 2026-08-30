from typing import Protocol

from src.domain.entities.registration_question import RegistrationQuestion


class RegistrationQuestionRepository(Protocol):
    async def get_by_id(self, question_id: int) -> RegistrationQuestion | None: ...

    async def get_active_by_trainer_id(
        self, trainer_id: int
    ) -> list[RegistrationQuestion]: ...

    async def get_all_by_trainer_id(
        self, trainer_id: int
    ) -> list[RegistrationQuestion]: ...

    async def get_by_trainer_and_system_key(
        self, trainer_id: int, system_key: str
    ) -> RegistrationQuestion | None: ...

    async def save(self, question: RegistrationQuestion) -> RegistrationQuestion: ...
    
    async def delete(self, question_id: int) -> None: ...
