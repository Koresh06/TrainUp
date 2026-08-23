from dataclasses import dataclass
from datetime import date

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.enums.slot import SlotStatus
from src.domain.repositories.booking import BookingRepository
from src.domain.services.calendar_service import CalendarService


@dataclass(frozen=True, eq=False)
class GetDayAvailabilityMapRequest(UseCaseRequest):
    trainer_id: int
    days_ahead: int = 30


@dataclass(kw_only=True)
class GetDayAvailabilityMapUseCase(UseCase[GetDayAvailabilityMapRequest, dict[date, int]]):
    calendar_service: CalendarService
    booking_repo: BookingRepository

    async def __call__(self, command: GetDayAvailabilityMapRequest) -> dict[date, int]:
        all_slots = await self.calendar_service.get_week_grid_slots(
            trainer_id=command.trainer_id,
            days_ahead=command.days_ahead,
        )
        # исключаем заблокированные тренером
        open_slots = [s for s in all_slots if s.status != SlotStatus.BLOCKED]

        slot_ids = [s.id for s in open_slots]
        booked_counts = await self.booking_repo.count_active_by_slot_ids(slot_ids)

        result: dict[date, int] = {}
        for slot in open_slots:
            free_spots = slot.capacity - booked_counts.get(slot.id, 0)
            if free_spots > 0:
                result[slot.slot_date] = result.get(slot.slot_date, 0) + free_spots
        return result