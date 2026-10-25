import logging
from dataclasses import dataclass
from datetime import date, timedelta

from src.application.interfaces.booking_scheduler import BookingScheduler
from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.recurring_booking._shared import _create_recurring_occurrence
from src.domain.entities.recurring_booking import RecurringBooking
from src.domain.enums.slot import SlotStatus
from src.domain.exception.base import DomainError
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.recurring_booking import RecurringBookingRepository
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.repositories.trainer_pricing_rule import TrainerPricingRuleRepository
from src.domain.repositories.trainer_reminder_settings import TrainerReminderSettingsRepository
from src.domain.repositories.trainer_vacation import TrainerVacationRepository
from src.domain.services.calendar_service import CalendarService
from src.domain.utils import get_project_today
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class MaintainRecurringBookingsRequest(UseCaseRequest):
    pass


@dataclass(kw_only=True)
class MaintainRecurringBookingsUseCase(UseCase[MaintainRecurringBookingsRequest, None]):
    recurring_repo: RecurringBookingRepository
    booking_repo: BookingRepository
    slot_repo: CalendarSlotRepository
    calendar_service: CalendarService
    trainer_repo: TrainerRepository
    client_repo: ClientRepository
    reminder_settings_repo: TrainerReminderSettingsRepository
    pricing_rule_repo: TrainerPricingRuleRepository
    notification_service: NotificationService
    booking_scheduler: BookingScheduler
    vacation_repo: TrainerVacationRepository
    subscription_repo: TrainerSubscriptionRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: MaintainRecurringBookingsRequest) -> None:
        recurring_bookings = await self.recurring_repo.get_all_active()
        today = get_project_today()
        created_count = 0
        # подписка проверяется один раз на тренера, а не на каждую постоянку
        trainer_available: dict[int, bool] = {}

        for recurring in recurring_bookings:
            if recurring.trainer_id not in trainer_available:
                trainer_available[recurring.trainer_id] = await self._is_trainer_available(
                    recurring.trainer_id
                )
            if not trainer_available[recurring.trainer_id]:
                # подписка кончилась или тренер заблокирован — новые тренировки
                # не создаём (и клиентам о них не пишем). Сама постоянка остаётся:
                # после продления всё продолжится с ближайшей недели
                continue

            latest = await self.booking_repo.get_latest_by_recurring_booking_id(recurring.id)

            # ближайшее вхождение ещё впереди — ждём, пока пройдёт. Статус не важен:
            # отменённая тренером/клиентом тренировка на эту неделю не должна
            # тут же пересоздаваться заново.
            if latest is not None:
                latest_slot = await self.slot_repo.get_by_id(latest.slot_id)
                if latest_slot is not None and latest_slot.slot_date >= today:
                    continue

            next_date = self._next_weekday_date(today, recurring.weekday)
            vacations = await self.vacation_repo.get_by_trainer(recurring.trainer_id, today)
            if any(v.covers(next_date) for v in vacations):
                # тренер в отпуске — тренировку не создаём и не шумим об этом
                continue
            slot = await self.slot_repo.get_by_date_and_time(
                recurring.trainer_id, next_date, recurring.start_time
            )
            if slot is None or not slot.is_active or slot.status == SlotStatus.BLOCKED:
                await self._notify_trainer_slot_unavailable(recurring, next_date)
                continue

            try:
                await _create_recurring_occurrence(
                    recurring=recurring,
                    slot=slot,
                    booking_repo=self.booking_repo,
                    calendar_service=self.calendar_service,
                    pricing_rule_repo=self.pricing_rule_repo,
                    reminder_settings_repo=self.reminder_settings_repo,
                    client_repo=self.client_repo,
                    trainer_repo=self.trainer_repo,
                    notification_service=self.notification_service,
                    booking_scheduler=self.booking_scheduler,
                    transaction_manager=self.transaction_manager,
                )
            except DomainError as error:
                # одна сломанная постоянка не должна останавливать обработку остальных
                await self.transaction_manager.rollback()
                logger.warning(
                    "[MaintainRecurringBookings:skip] recurring_id=%s error=%s",
                    recurring.id, error.message,
                )
                await self._notify_trainer_slot_unavailable(recurring, next_date)
                continue
            created_count += 1

        logger.info(
            "[MaintainRecurringBookings:done] checked=%s created=%s skipped_trainers=%s",
            len(recurring_bookings), created_count,
            sum(1 for available in trainer_available.values() if not available),
        )

    async def _is_trainer_available(self, trainer_id: int) -> bool:
        trainer = await self.trainer_repo.get_by_id(trainer_id)
        if trainer is None or not trainer.is_active:
            return False
        return await self.subscription_repo.get_active_by_trainer_id(trainer_id) is not None

    async def _notify_trainer_slot_unavailable(
        self, recurring: RecurringBooking, next_date: date
    ) -> None:
        trainer = await self.trainer_repo.get_by_id(recurring.trainer_id)
        if trainer is None:
            return
        await self.notification_service.send(
            chat_id=trainer.notification_chat_id,
            fallback_chat_id=trainer.tg_id,
            text=(
                f"⚠️ Не удалось автоматически создать постоянную тренировку "
                f"на {next_date.strftime('%d.%m.%Y')} "
                f"{recurring.start_time.strftime('%H:%M')} — "
                f"в это время нет доступного слота в расписании "
                f"(время убрано из шаблона или заблокировано)."
            ),
        )

    @staticmethod
    def _next_weekday_date(from_date: date, weekday: int) -> date:
        days_ahead = (weekday - from_date.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return from_date + timedelta(days=days_ahead)
