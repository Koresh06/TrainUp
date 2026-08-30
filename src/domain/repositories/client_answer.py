from typing import Protocol

from src.domain.entities.client_answer import ClientAnswer


class ClientAnswerRepository(Protocol):
    async def get_by_client_id(self, client_id: int) -> list[ClientAnswer]: ...

    async def save(self, answer: ClientAnswer) -> ClientAnswer: ...
    
    async def save_many(self, answers: list[ClientAnswer]) -> list[ClientAnswer]: ...