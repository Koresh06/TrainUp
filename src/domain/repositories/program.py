from typing import Protocol

from src.domain.entities.program import ProgramRequest


class ProgramRequestRepository(Protocol):
    async def get_all(self) -> list[ProgramRequest]:
        ...

    async def get_by_id(self, program_request_id: int) -> ProgramRequest | None:
        ...

    async def save(self, program_request: ProgramRequest) -> ProgramRequest:
        ...

    async def delete(self, program_request_id: int) -> None:
        ...