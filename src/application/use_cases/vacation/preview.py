from dataclasses import dataclass, field
from datetime import date

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.vacation._shared import period_slots_and_bookings
from src.domain.enums.slot import SlotStatus
from src.domain.repositories.booking import BookingRepository, BookingView
from src.domain.repositories.calendar_slot import CalendarSlotRepository


@dataclass(frozen=True)
class VacationPreviewDTO:
    slots_to_block: int
    bookings: list[BookingView] = field(default_factory=list)

    @property
    def offline_clients(self) -> list[str]:
        return sorted({v.client_full_name for v in self.bookings if not v.client_has_telegram})


@dataclass(frozen=True, eq=False)
class PreviewVacationRequest(UseCaseRequest):
    trainer_id: int
    date_from: date
    date_to: date


@dataclass(kw_only=True)
class PreviewVacationUseCase(UseCase[PreviewVacationRequest, VacationPreviewDTO]):
    """Что произойдёт, если закрыть период: сколько слотов и чьи записи отменятся."""

    slot_repo: CalendarSlotRepository
    booking_repo: BookingRepository

    async def __call__(self, command: PreviewVacationRequest) -> VacationPreviewDTO:
        slots, views = await period_slots_and_bookings(
            trainer_id=command.trainer_id,
            date_from=command.date_from,
            date_to=command.date_to,
            slot_repo=self.slot_repo,
            booking_repo=self.booking_repo,
        )
        return VacationPreviewDTO(
            slots_to_block=sum(1 for s in slots if s.status != SlotStatus.BLOCKED),
            bookings=views,
        )
