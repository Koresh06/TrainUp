import logging
from dataclasses import dataclass
from datetime import date

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.enums.slot import SlotStatus
from src.domain.services.calendar_service import CalendarService
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class SetDayBlockedRequest(UseCaseRequest):
    trainer_id: int
    slot_date: date
    blocked: bool


@dataclass(kw_only=True)
class SetDayBlockedUseCase(UseCase[SetDayBlockedRequest, int]):
    """Блокирует/разблокирует все слоты дня. Возвращает число изменённых слотов."""

    calendar_service: CalendarService
    transaction_manager: TransactionManager

    async def __call__(self, command: SetDayBlockedRequest) -> int:
        slots = await self.calendar_service.get_slots_for_date(
            command.trainer_id, command.slot_date
        )
        changed = 0
        for slot in slots:
            is_blocked = slot.status == SlotStatus.BLOCKED
            if is_blocked == command.blocked:
                continue
            if command.blocked:
                await self.calendar_service.block_slot(slot.id)
            else:
                await self.calendar_service.unblock_slot(slot.id)
            changed += 1
        await self.transaction_manager.commit()

        logger.info(
            "[SetDayBlocked:done] trainer_id=%s date=%s blocked=%s changed=%s",
            command.trainer_id, command.slot_date, command.blocked, changed,
        )
        return changed
