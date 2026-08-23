from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.repositories.booking import BookingRepository


@dataclass(frozen=True, eq=False)
class CountActiveBookingsBySlotIdsRequest(UseCaseRequest):
    slot_ids: list[int]


@dataclass(kw_only=True)
class CountActiveBookingsBySlotIdsUseCase(
    UseCase[CountActiveBookingsBySlotIdsRequest, dict[int, int]]
):
    booking_repo: BookingRepository

    async def __call__(self, command: CountActiveBookingsBySlotIdsRequest) -> dict[int, int]:
        return await self.booking_repo.count_active_by_slot_ids(command.slot_ids)