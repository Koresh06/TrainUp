import logging
from dataclasses import dataclass

from src.domain.entities.booking import Booking
from src.domain.entities.calendar_slot import CalendarSlot
from src.domain.entities.client import Client
from src.domain.entities.trainer import Trainer
from src.domain.enums.booking import BookingStatus
from src.domain.constants import DEFAULT_MAX_ACTIVE_BOOKINGS
from src.domain.exception.booking import (
    ActiveBookingsLimitExceededException,
    ClientAlreadyBookedThisSlotException,
)
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.client_answer import ClientAnswerRepository
from src.domain.repositories.registration_question import RegistrationQuestionRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.repositories.trainer_booking_settings import (
    TrainerBookingSettingsRepository,
)
from src.domain.repositories.trainer_pricing_rule import TrainerPricingRuleRepository
from src.domain.services.calendar_service import CalendarService
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.interfaces.notification_service import (
    NotificationService,
    NewBookingNotificationDTO,
)
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class CreateBookingRequest(UseCaseRequest):
    client_id: int
    trainer_id: int
    slot_id: int


@dataclass(kw_only=True)
class CreateBookingUseCase(UseCase[CreateBookingRequest, Booking]):
    calendar_service: CalendarService
    booking_repo: BookingRepository
    trainer_repo: TrainerRepository
    client_repo: ClientRepository
    pricing_rule_repo: TrainerPricingRuleRepository
    booking_settings_repo: TrainerBookingSettingsRepository
    answer_repo: ClientAnswerRepository
    question_repo: RegistrationQuestionRepository
    notification_service: NotificationService
    transaction_manager: TransactionManager

    async def __call__(self, command: CreateBookingRequest) -> Booking:
        logger.info(
            "[CreateBooking] client_id=%s trainer_id=%s slot_id=%s",
            command.client_id,
            command.trainer_id,
            command.slot_id,
        )

        already_booked = await self.booking_repo.exists_active_by_client_and_slot(
            command.client_id, command.slot_id
        )
        if already_booked:
            raise ClientAlreadyBookedThisSlotException(
                client_id=command.client_id,
                slot_id=command.slot_id,
            )

        await self._ensure_active_bookings_limit(command)

        slot: CalendarSlot = await self.calendar_service.book_slot(command.slot_id)

        pricing_rule = await self.pricing_rule_repo.get_by_trainer_id(
            command.trainer_id
        )
        price = (
            pricing_rule.price_for(slot.start_time)
            if pricing_rule is not None
            else None
        )

        booking = Booking(
            client_id=command.client_id,
            trainer_id=command.trainer_id,
            slot_id=command.slot_id,
            status=BookingStatus.PENDING,
            price=price,
        )
        saved = await self.booking_repo.save(booking)
        await self.transaction_manager.commit()

        trainer: Trainer | None = await self.trainer_repo.get_by_id(command.trainer_id)
        client: Client | None = await self.client_repo.get_by_id(command.client_id)
        if trainer is not None and client is not None:
            await self.notification_service.notify_new_booking(
                NewBookingNotificationDTO(
                    chat_id=trainer.notification_chat_id,
                    fallback_chat_id=trainer.tg_id,
                    booking_id=saved.id,
                    date_label=slot.slot_date.strftime("%d.%m.%Y"),
                    time_label=slot.start_time.strftime("%H:%M"),
                    client_first_name=client.first_name,
                    client_last_name=client.last_name,
                    client_username=client.username,
                    client_phone=client.phone,
                    client_age=client.age,
                    client_answers=await self._client_answers(client.id, trainer.id),
                )
            )

        logger.info("[CreateBooking:done] booking_id=%s", saved.id)
        return saved

    async def _ensure_active_bookings_limit(self, command: CreateBookingRequest) -> None:
        settings = await self.booking_settings_repo.get_by_trainer_id(command.trainer_id)
        limit = (
            settings.max_active_bookings_per_client
            if settings is not None
            else DEFAULT_MAX_ACTIVE_BOOKINGS
        )
        upcoming = await self.booking_repo.get_upcoming_by_client(command.client_id)
        # тренировки постоянного клиента назначает тренер — в лимит самостоятельных
        # записей клиента они не входят
        own_active = [b for b in upcoming if b.recurring_booking_id is None]
        if len(own_active) >= limit:
            raise ActiveBookingsLimitExceededException(
                client_id=command.client_id, limit=limit
            )

    async def _client_answers(self, client_id: int, trainer_id: int) -> list[tuple[str, str]]:
        questions = await self.question_repo.get_all_by_trainer_id(trainer_id)
        answers = await self.answer_repo.get_by_client_id(client_id)
        answers_by_question = {a.question_id: a.value for a in answers}
        return [
            (q.label, ", ".join(answers_by_question[q.id]))
            for q in questions
            if answers_by_question.get(q.id)
        ]
