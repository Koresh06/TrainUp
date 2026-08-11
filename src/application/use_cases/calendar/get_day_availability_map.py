from dataclasses import dataclass
from datetime import date

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.services.calendar_service import CalendarService


@dataclass(frozen=True, eq=False)
class GetDayAvailabilityMapRequest(UseCaseRequest):
    trainer_id: int
    days_ahead: int = 30


@dataclass(kw_only=True)
class GetDayAvailabilityMapUseCase(UseCase[GetDayAvailabilityMapRequest, dict[date, int]]):
    calendar_service: CalendarService

    async def __call__(self, command: GetDayAvailabilityMapRequest) -> dict[date, int]:
        free_slots = await self.calendar_service.get_free_slots(
            trainer_id=command.trainer_id,
            days_ahead=command.days_ahead,
        )
        result: dict[date, int] = {}
        for slot in free_slots:
            result[slot.slot_date] = result.get(slot.slot_date, 0) + 1
        return result