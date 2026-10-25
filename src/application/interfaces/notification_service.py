from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Protocol

from src.domain.enums.request import ClientRequestKind


@dataclass(frozen=True)
class NewBookingNotificationDTO:
    chat_id: int
    booking_id: int
    date_label: str
    time_label: str
    client_first_name: str
    client_last_name: str | None
    client_username: str | None
    client_phone: str | None
    client_age: int | None
    client_answers: list[tuple[str, str]] = field(default_factory=list)  # (вопрос, ответ)
    # личка тренера — если в рабочую группу доставить не удалось
    fallback_chat_id: int | None = None


@dataclass(frozen=True)
class TrainingReminderNotificationDTO:
    chat_id: int
    date_label: str
    time_label: str
    trainer_name: str
    minutes_before: int
    booking_id: int


@dataclass(frozen=True)
class ClientRequestNotificationDTO:
    chat_id: int
    kind: ClientRequestKind
    request_id: int
    title: str
    details: str
    client_full_name: str
    client_tg_id: int
    client_username: str | None
    client_phone: str | None
    # личка тренера — если в рабочую группу доставить не удалось
    fallback_chat_id: int | None = None


@dataclass(frozen=True)
class PlanNextTrainingNotificationDTO:
    chat_id: int
    trainer_name: str
    days_since_training: int


@dataclass(frozen=True)
class AttendanceRequestDTO:
    """Накануне: «Завтра в 18:00 тренировка — придёте?»."""

    chat_id: int
    booking_id: int
    trainer_name: str
    day_label: str  # «четверг 22 октября»
    time_label: str
    is_tomorrow: bool = True


@dataclass(frozen=True)
class RatingRequestDTO:
    """После тренировки: «Как прошла тренировка?» ⭐1–5."""

    chat_id: int
    booking_id: int
    trainer_name: str
    date_label: str


@dataclass(frozen=True)
class DigestItemDTO:
    time_label: str
    client_name: str
    is_pending: bool = False
    is_recurring: bool = False
    is_offline: bool = False
    trainer_note: str | None = None
    # клиент ответил «приду» на запрос накануне
    client_confirmed: bool = False


@dataclass(frozen=True)
class TrainerDigestDTO:
    """Сводка тренеру: утром — на сегодня, вечером — на завтра."""

    chat_id: int
    day: date
    day_label: str  # «среда 22 октября»
    is_tomorrow: bool
    items: list[DigestItemDTO]
    expected_income: Decimal = Decimal("0")
    # все будущие записи, которые тренер ещё не подтвердил
    pending_total: int = 0


class SubscriptionEvent(str, Enum):
    WARNING = "warning"  # скоро закончится
    EXPIRED = "expired"  # закончилась — кабинет и запись клиентов закрыты
    GRANTED = "granted"  # админ выдал подписку
    PAID = "paid"        # оплата подтверждена — подписка активна


@dataclass(frozen=True)
class SubscriptionNotificationDTO:
    chat_id: int
    event: SubscriptionEvent
    expired_at: datetime
    hours_left: int = 0
    # заканчивается бесплатный пробный период — другой текст: тренер ещё ни разу не платил
    is_trial: bool = False


@dataclass(frozen=True)
class ManualPaymentRequestDTO:
    """Заявка на ручную оплату — админам с кнопками «получена / отклонить»."""

    external_id: str
    trainer_name: str
    trainer_tg_id: int
    trainer_phone: str | None
    plan_label: str
    amount_label: str


@dataclass(frozen=True)
class MailingResultDTO:
    success: int
    blocked: int
    failed: int


class NotificationService(Protocol):
    async def send(
        self, *, chat_id: int, text: str, fallback_chat_id: int | None = None
    ) -> None:
        """fallback_chat_id — куда отправить, если chat_id недоступен (бота
        удалили из рабочей группы тренера — дублируем тренеру в личку)."""
        ...

    async def notify_new_booking(self, data: NewBookingNotificationDTO) -> None: ...

    async def notify_training_reminder(
        self, data: TrainingReminderNotificationDTO
    ) -> None: ...

    async def notify_client_request(self, data: ClientRequestNotificationDTO) -> None: ...

    async def notify_plan_next_training(
        self, data: PlanNextTrainingNotificationDTO
    ) -> None: ...

    async def notify_subscription(self, data: SubscriptionNotificationDTO) -> None: ...

    async def notify_trainer_digest(self, data: TrainerDigestDTO) -> None: ...

    async def notify_attendance_request(self, data: AttendanceRequestDTO) -> None: ...

    async def notify_rating_request(self, data: RatingRequestDTO) -> None: ...

    async def notify_admins(self, text: str) -> None: ...

    async def broadcast_copy(
        self, *, chat_ids: list[int], from_chat_id: int, message_id: int
    ) -> MailingResultDTO: ...

    async def notify_manual_payment_request(self, data: ManualPaymentRequestDTO) -> None: ...
