import logging
from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.vacation._shared import period_slots_and_bookings
from src.domain.entities.trainer_vacation import TrainerVacation
from src.domain.enums.slot import SlotStatus
from src.domain.exception.vacation import VacationNotFoundException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.trainer_vacation import TrainerVacationRepository
from src.domain.services.calendar_service import CalendarService
from src.domain.utils import get_project_today
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class GetVacationsRequest(UseCaseRequest):
    trainer_id: int


@dataclass(kw_only=True)
class GetVacationsUseCase(UseCase[GetVacationsRequest, list[TrainerVacation]]):
    vacation_repo: TrainerVacationRepository

    async def __call__(self, command: GetVacationsRequest) -> list[TrainerVacation]:
        return await self.vacation_repo.get_by_trainer(command.trainer_id, get_project_today())


@dataclass(frozen=True, eq=False)
class DeleteVacationRequest(UseCaseRequest):
    trainer_id: int
    vacation_id: int


@dataclass(kw_only=True)
class DeleteVacationUseCase(UseCase[DeleteVacationRequest, int]):
    """
    Вышел из отпуска раньше: период удаляется, будущие слоты в нём снова
    открываются (в том числе закрытые вручную — отдельно их не различаем).
    Отменённые записи не восстанавливаются.
    """

    vacation_repo: TrainerVacationRepository
    slot_repo: CalendarSlotRepository
    booking_repo: BookingRepository
    calendar_service: CalendarService
    transaction_manager: TransactionManager

    async def __call__(self, command: DeleteVacationRequest) -> int:
        vacation = await self.vacation_repo.get_by_id(command.vacation_id)
        if vacation is None or vacation.trainer_id != command.trainer_id:
            raise VacationNotFoundException(vacation_id=command.vacation_id)

        await self.vacation_repo.delete(vacation.id)
        slots, _ = await period_slots_and_bookings(
            trainer_id=command.trainer_id,
            date_from=vacation.date_from,
            date_to=vacation.date_to,
            slot_repo=self.slot_repo,
            booking_repo=self.booking_repo,
        )
        opened = 0
        for slot in slots:
            if slot.status == SlotStatus.BLOCKED:
                await self.calendar_service.unblock_slot(slot.id)
                opened += 1
        await self.transaction_manager.commit()
        logger.info("[DeleteVacation:done] vacation_id=%s opened=%s", vacation.id, opened)
        return opened
