from dataclasses import dataclass
from datetime import date

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.enums.booking import BookingStatus
from src.domain.repositories.booking import BookingRepository, BookingView


@dataclass(frozen=True, eq=False)
class GetBookingViewsRequest(UseCaseRequest):
    """Записи тренера со слотом и клиентом — для расписания, истории и карточки клиента."""

    trainer_id: int
    date_from: date | None = None
    date_to: date | None = None
    statuses: tuple[BookingStatus, ...] | None = None
    client_id: int | None = None
    newest_first: bool = False
    limit: int | None = None


@dataclass(kw_only=True)
class GetBookingViewsUseCase(UseCase[GetBookingViewsRequest, list[BookingView]]):
    booking_repo: BookingRepository

    async def __call__(self, command: GetBookingViewsRequest) -> list[BookingView]:
        return await self.booking_repo.get_views(
            trainer_id=command.trainer_id,
            date_from=command.date_from,
            date_to=command.date_to,
            statuses=command.statuses,
            client_id=command.client_id,
            newest_first=command.newest_first,
            limit=command.limit,
        )
