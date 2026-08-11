from dataclasses import dataclass
from datetime import date

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.services.calendar_service import CalendarService


@dataclass(frozen=True, eq=False)
class GetDaySlotsRequest(UseCaseRequest):
    trainer_id: int
    slot_date: date


@dataclass(kw_only=True)
class GetDaySlotsUseCase(UseCase[GetDaySlotsRequest, list[CalendarSlot]]):
    calendar_service: CalendarService

    async def __call__(self, command: GetDaySlotsRequest) -> list[CalendarSlot]:
        return await self.calendar_service.get_slots_for_date(
            trainer_id=command.trainer_id,
            slot_date=command.slot_date,
        )