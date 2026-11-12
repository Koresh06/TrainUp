from dataclasses import dataclass

from src.application.interfaces.booking_scheduler import BookingScheduler
from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest

from src.application.use_cases.recurring_booking._shared import _create_recurring_occurrence
from src.domain.entities.booking import Booking
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.recurring_booking import RecurringBooking
from src.domain.exception.base import DomainError
from src.domain.exception.calendar_slot import (
    CalendarSlotNotFoundException,
    SlotInPastException,
)
from src.domain.exception.recurring_booking import RecurringBookingAlreadyExistsException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.recurring_booking import RecurringBookingRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.repositories.trainer_pricing_rule import TrainerPricingRuleRepository
from src.domain.repositories.trainer_reminder_settings import TrainerReminderSettingsRepository
from src.domain.services.calendar_service import CalendarService
from src.domain.utils import is_slot_in_past
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class AddRecurringBookingRequest(UseCaseRequest):
    trainer_id: int
    client_id: int
    slot_id: int


@dataclass(kw_only=True)
class AddRecurringBookingUseCase(UseCase[AddRecurringBookingRequest, Booking]):
    recurring_repo: RecurringBookingRepository
    slot_repo: CalendarSlotRepository
    booking_repo: BookingRepository
    calendar_service: CalendarService
    pricing_rule_repo: TrainerPricingRuleRepository
    client_repo: ClientRepository
    trainer_repo: TrainerRepository
    reminder_settings_repo: TrainerReminderSettingsRepository
    notification_service: NotificationService
    booking_scheduler: BookingScheduler
    transaction_manager: TransactionManager

    async def __call__(self, command: AddRecurringBookingRequest) -> Booking:
        slot = await self.slot_repo.get_by_id(command.slot_id)
        if slot is None:
            raise CalendarSlotNotFoundException(command.slot_id)
        # проверяем до сохранения шаблона, чтобы не осталось постоянки без тренировки
        if is_slot_in_past(slot):
            raise SlotInPastException(command.slot_id)

        weekday = slot.slot_date.weekday()
        existing = next(
            (
                r
                for r in await self.recurring_repo.get_active_by_trainer_and_client(
                    trainer_id=command.trainer_id, client_id=command.client_id
                )
                if r.weekday == weekday and r.start_time == slot.start_time
            ),
            None,
        )
        if existing is not None:
            # постоянка уже есть, но её ближайшая тренировка отменена (или не
            # создалась) — возвращаем тренировку в расписание, а не заставляем
            # тренера останавливать постоянку и заводить её заново
            upcoming = await self.booking_repo.get_upcoming_by_recurring_booking_id(
                existing.id
            )
            if upcoming:
                raise RecurringBookingAlreadyExistsException(
                    trainer_id=command.trainer_id,
                    client_id=command.client_id,
                    weekday=weekday,
                    start_time=slot.start_time,
                )
            return await self._create_occurrence(existing, slot)

        recurring = RecurringBooking(
            trainer_id=command.trainer_id,
            client_id=command.client_id,
            weekday=weekday,
            start_time=slot.start_time,
            is_active=True,
        )
        # без отдельного commit: шаблон и первая тренировка сохраняются вместе.
        # Иначе при недоступном слоте оставалась постоянка без тренировки, а
        # повторное добавление упиралось в «уже есть постоянная запись»
        saved_recurring: RecurringBooking = await self.recurring_repo.save(recurring)
        return await self._create_occurrence(saved_recurring, slot)

    async def _create_occurrence(
        self, recurring: RecurringBooking, slot: CalendarSlot
    ) -> Booking:
        try:
            return await _create_recurring_occurrence(
                recurring=recurring,
                slot=slot,
                booking_repo=self.booking_repo,
                calendar_service=self.calendar_service,
                pricing_rule_repo=self.pricing_rule_repo,
                client_repo=self.client_repo,
                trainer_repo=self.trainer_repo,
                reminder_settings_repo=self.reminder_settings_repo,
                notification_service=self.notification_service,
                booking_scheduler=self.booking_scheduler,
                transaction_manager=self.transaction_manager,
            )
        except DomainError:
            await self.transaction_manager.rollback()
            raise
