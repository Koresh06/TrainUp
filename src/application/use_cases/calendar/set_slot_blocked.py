import logging
from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.services.calendar_service import CalendarService
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class SetSlotBlockedRequest(UseCaseRequest):
    slot_id: int
    blocked: bool


@dataclass(kw_only=True)
class SetSlotBlockedUseCase(UseCase[SetSlotBlockedRequest, CalendarSlot]):
    """
    Ручная блокировка/разблокировка слота тренером. Блокировка закрывает слот
    только для новых записей — уже существующие брони сохраняются, тренер
    отменяет/переносит их сам в «Расписании».
    """

    calendar_service: CalendarService
    transaction_manager: TransactionManager

    async def __call__(self, command: SetSlotBlockedRequest) -> CalendarSlot:
        if command.blocked:
            slot = await self.calendar_service.block_slot(command.slot_id)
        else:
            slot = await self.calendar_service.unblock_slot(command.slot_id)
        await self.transaction_manager.commit()

        logger.info(
            "[SetSlotBlocked:done] slot_id=%s blocked=%s", command.slot_id, command.blocked
        )
        return slot
