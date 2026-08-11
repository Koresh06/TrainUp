from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.exception.calendar_slot import CalendarSlotNotFoundException
from src.domain.repositories.calendar_slot import CalendarSlotRepository


@dataclass(frozen=True, eq=False)
class GetSlotByIdRequest(UseCaseRequest):
    slot_id: int


@dataclass(kw_only=True)
class GetSlotByIdUseCase(UseCase[GetSlotByIdRequest, CalendarSlot]):
    slot_repo: CalendarSlotRepository

    async def __call__(self, command: GetSlotByIdRequest) -> CalendarSlot:
        slot = await self.slot_repo.get_by_id(command.slot_id)
        if slot is None:
            raise CalendarSlotNotFoundException(command.slot_id)
        return slot