import logging
from dataclasses import dataclass
from html import escape

from src.application.interfaces.booking_scheduler import BookingScheduler
from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.booking._shared import _schedule_booking_jobs
from src.application.use_cases.client._shared import get_trainer_client
from src.domain.entities.booking import Booking
from src.domain.enums.booking import BookingStatus
from src.domain.exception.booking import ClientAlreadyBookedThisSlotException
from src.domain.exception.calendar_slot import CalendarSlotNotFoundException
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.repositories.trainer_pricing_rule import TrainerPricingRuleRepository
from src.domain.repositories.trainer_reminder_settings import (
    TrainerReminderSettingsRepository,
)
from src.domain.services.calendar_service import CalendarService
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class CreateBookingByTrainerRequest(UseCaseRequest):
    trainer_id: int
    client_id: int
    slot_id: int


@dataclass(kw_only=True)
class CreateBookingByTrainerUseCase(UseCase[CreateBookingByTrainerRequest, Booking]):
    """
    Тренер сам записывает клиента (в т.ч. без Telegram) в свободный слот своего
    расписания. Запись сразу подтверждена: подтверждать самому себе незачем,
    лимит активных записей клиента не проверяем — он защищает тренера от
    клиентов, а не наоборот. Вместимость слота проверяется как обычно.
    """

    calendar_service: CalendarService
    booking_repo: BookingRepository
    client_repo: ClientRepository
    trainer_repo: TrainerRepository
    slot_repo: CalendarSlotRepository
    pricing_rule_repo: TrainerPricingRuleRepository
    reminder_settings_repo: TrainerReminderSettingsRepository
    notification_service: NotificationService
    booking_scheduler: BookingScheduler
    transaction_manager: TransactionManager

    async def __call__(self, command: CreateBookingByTrainerRequest) -> Booking:
        client = await get_trainer_client(
            self.client_repo, client_id=command.client_id, trainer_id=command.trainer_id
        )
        slot = await self.slot_repo.get_by_id(command.slot_id)
        if slot is None or slot.trainer_id != command.trainer_id:
            raise CalendarSlotNotFoundException(command.slot_id)

        if await self.booking_repo.exists_active_by_client_and_slot(client.id, slot.id):
            raise ClientAlreadyBookedThisSlotException(client_id=client.id, slot_id=slot.id)

        slot = await self.calendar_service.book_slot(slot.id)

        pricing_rule = await self.pricing_rule_repo.get_by_trainer_id(command.trainer_id)
        booking = Booking(
            client_id=client.id,
            trainer_id=command.trainer_id,
            slot_id=slot.id,
            status=BookingStatus.CONFIRMED,
            price=pricing_rule.price_for(slot.start_time) if pricing_rule is not None else None,
        )
        saved = await self.booking_repo.save(booking)
        await self.transaction_manager.commit()

        if client.has_telegram:
            trainer = await self.trainer_repo.get_by_id(command.trainer_id)
            trainer_name = trainer.name if trainer is not None else "Тренер"
            await self.notification_service.send(
                chat_id=client.tg_id,
                text=(
                    f"📅 <b>{escape(trainer_name)} записал вас на тренировку</b>\n\n"
                    f"📅 {slot.slot_date.strftime('%d.%m.%Y')}\n"
                    f"🕐 {slot.start_time.strftime('%H:%M')}\n\n"
                    f"Запись — в «📋 Мои записи»."
                ),
            )

        await _schedule_booking_jobs(
            booking_id=saved.id,
            trainer_id=command.trainer_id,
            slot=slot,
            reminder_settings_repo=self.reminder_settings_repo,
            booking_scheduler=self.booking_scheduler,
            transaction_manager=self.transaction_manager,
            send_reminder=client.has_telegram,
        )
        logger.info(
            "[CreateBookingByTrainer:done] booking_id=%s client_id=%s", saved.id, client.id
        )
        return saved
