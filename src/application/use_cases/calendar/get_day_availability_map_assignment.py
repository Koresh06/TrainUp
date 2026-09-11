from dataclasses import dataclass
from datetime import date

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.enums.slot import SlotStatus
from src.domain.services.calendar_service import CalendarService


@dataclass(frozen=True, eq=False)
class GetDayAvailabilityMapForAssignmentRequest(UseCaseRequest):
    trainer_id: int
    days_ahead: int = 30


@dataclass(kw_only=True)
class GetDayAvailabilityMapForAssignmentUseCase(
    UseCase[GetDayAvailabilityMapForAssignmentRequest, dict[date, int]]
):
    calendar_service: CalendarService

    async def __call__(
        self, command: GetDayAvailabilityMapForAssignmentRequest
    ) -> dict[date, int]:
        all_slots = await self.calendar_service.get_week_grid_slots(
            trainer_id=command.trainer_id,
            days_ahead=command.days_ahead,
        )
        open_slots = [s for s in all_slots if s.status != SlotStatus.BLOCKED]

        result: dict[date, int] = {}
        for slot in open_slots:
            result[slot.slot_date] = result.get(slot.slot_date, 0) + 1
        return result