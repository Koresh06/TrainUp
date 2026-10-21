from dataclasses import dataclass
from datetime import date, timedelta

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.constants import INACTIVE_CLIENT_DAYS
from src.domain.entities.client import Client
from src.domain.enums.booking import ACTIVE_BOOKING_STATUSES, BookingStatus
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.recurring_booking import RecurringBookingRepository
from src.domain.utils import get_project_today


@dataclass(frozen=True)
class InactiveClientDTO:
    client: Client
    last_visit: date

    @property
    def days_since(self) -> int:
        return (get_project_today() - self.last_visit).days


@dataclass(frozen=True, eq=False)
class GetInactiveClientsRequest(UseCaseRequest):
    trainer_id: int
    days: int = INACTIVE_CLIENT_DAYS


@dataclass(kw_only=True)
class GetInactiveClientsUseCase(UseCase[GetInactiveClientsRequest, list[InactiveClientDTO]]):
    """
    Клиенты, которые ходили, но пропали: последняя проведённая тренировка
    старше N дней, будущих записей нет и постоянной записи тоже. Самые
    «потерянные» — первыми.
    """

    client_repo: ClientRepository
    booking_repo: BookingRepository
    recurring_repo: RecurringBookingRepository

    async def __call__(self, command: GetInactiveClientsRequest) -> list[InactiveClientDTO]:
        today = get_project_today()
        views = await self.booking_repo.get_views(
            trainer_id=command.trainer_id,
            statuses=(BookingStatus.COMPLETED, *ACTIVE_BOOKING_STATUSES),
        )
        last_visit: dict[int, date] = {}
        busy: set[int] = set()
        for v in views:
            cid = v.booking.client_id
            if v.booking.status == BookingStatus.COMPLETED:
                last_visit[cid] = max(last_visit.get(cid, v.slot_date), v.slot_date)
            elif v.slot_date >= today:
                busy.add(cid)
        recurring = {
            r.client_id for r in await self.recurring_repo.get_active_by_trainer_id(command.trainer_id)
        }
        threshold = today - timedelta(days=command.days)

        result = [
            InactiveClientDTO(client=c, last_visit=last_visit[c.id])
            for c in await self.client_repo.get_by_trainer_id(command.trainer_id)
            if c.is_active
            and c.id in last_visit
            and last_visit[c.id] < threshold
            and c.id not in busy
            and c.id not in recurring
        ]
        return sorted(result, key=lambda dto: dto.last_visit)
