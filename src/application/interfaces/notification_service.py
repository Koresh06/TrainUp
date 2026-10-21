from dataclasses import dataclass, field
from datetime import datetime
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


@dataclass(frozen=True)
class PlanNextTrainingNotificationDTO:
    chat_id: int
    trainer_name: str
    days_since_training: int


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
    async def send(self, *, chat_id: int, text: str) -> None: ...

    async def notify_new_booking(self, data: NewBookingNotificationDTO) -> None: ...

    async def notify_training_reminder(
        self, data: TrainingReminderNotificationDTO
    ) -> None: ...

    async def notify_client_request(self, data: ClientRequestNotificationDTO) -> None: ...

    async def notify_plan_next_training(
        self, data: PlanNextTrainingNotificationDTO
    ) -> None: ...

    async def notify_subscription(self, data: SubscriptionNotificationDTO) -> None: ...

    async def notify_admins(self, text: str) -> None: ...

    async def broadcast_copy(
        self, *, chat_ids: list[int], from_chat_id: int, message_id: int
    ) -> MailingResultDTO: ...

    async def notify_manual_payment_request(self, data: ManualPaymentRequestDTO) -> None: ...
