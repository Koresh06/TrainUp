from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.services.calendar_service import CalendarService


@dataclass(frozen=True, eq=False)
class GetAvailableSlotsRequest(UseCaseRequest):
    trainer_id: int
    days_ahead: int = 6


@dataclass(kw_only=True)
class GetAvailableSlotsUseCase(UseCase[GetAvailableSlotsRequest, list[CalendarSlot]]):
    calendar_service: CalendarService

    async def __call__(self, command: GetAvailableSlotsRequest) -> list[CalendarSlot]:
        return await self.calendar_service.get_free_slots(
            trainer_id=command.trainer_id,
            days_ahead=command.days_ahead,
        )