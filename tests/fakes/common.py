"""In-memory фейки репозиториев и портов для тестов application-слоя."""

from datetime import datetime

from src.application.interfaces.mailing_progress import MailingProgressDTO
from src.application.interfaces.notification_service import MailingResultDTO
from src.domain.entities.client import Client
from src.domain.entities.trainer import Trainer
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.subscription import SubscriptionStatus


class _IdRepo:
    def __init__(self, items=None) -> None:
        self.items: dict[int, object] = {}
        self._next_id = 1
        for item in items or []:
            if item.id == 0:
                item.id = self._next_id
            self.items[item.id] = item
            self._next_id = max(self._next_id, item.id + 1)

    async def get_by_id(self, item_id: int):
        return self.items.get(item_id)

    async def get_all(self):
        return list(self.items.values())

    async def save(self, item):
        if item.id == 0:
            item.id = self._next_id
            self._next_id += 1
        self.items[item.id] = item
        return item


class FakeTrainers(_IdRepo):
    async def get_by_tg_id(self, tg_id: int) -> Trainer | None:
        return next((t for t in self.items.values() if t.tg_id == tg_id), None)

    async def get_all_active(self) -> list[Trainer]:
        return [t for t in self.items.values() if t.is_active]


class FakeClients(_IdRepo):
    async def get_by_tg_id(self, tg_id: int) -> Client | None:
        return next((c for c in self.items.values() if c.tg_id == tg_id), None)

    async def get_by_trainer_id(self, trainer_id: int) -> list[Client]:
        return [c for c in self.items.values() if c.trainer_id == trainer_id]


class FakeSubscriptions(_IdRepo):
    async def get_active_by_trainer_id(self, trainer_id: int) -> TrainerSubscription | None:
        active = [
            s for s in self.items.values() if s.trainer_id == trainer_id and s.is_active()
        ]
        return max(active, key=lambda s: s.expired_at) if active else None

    async def get_all_by_status(self, status: SubscriptionStatus) -> list[TrainerSubscription]:
        return [s for s in self.items.values() if s.status == status]

    async def get_by_trainer_id(self, trainer_id: int) -> list[TrainerSubscription]:
        return [s for s in self.items.values() if s.trainer_id == trainer_id]


class FakePricePlans(_IdRepo):
    async def get_active_plans(self):
        return [p for p in self.items.values() if p.is_active]


class FakeTaskQueue:
    def __init__(self) -> None:
        self.enqueued: list[tuple[str, tuple]] = []
        self.scheduled: list[tuple[str, tuple, datetime]] = []

    async def enqueue(self, *, task_name: str, args: tuple) -> str:
        self.enqueued.append((task_name, args))
        return f"task-{len(self.enqueued)}"

    async def schedule(self, *, task_name: str, args: tuple, run_at_utc: datetime) -> str:
        self.scheduled.append((task_name, args, run_at_utc))
        return f"job-{len(self.scheduled)}"

    async def cancel(self, *, job_id: str) -> None: ...


class FakeProgressStore:
    def __init__(self) -> None:
        self.totals: dict[str, list[int]] = {}
        self.cleared: list[str] = []

    async def add_batch_result(self, *, mailing_id, success, blocked, failed) -> MailingProgressDTO:
        done, s, b, f = self.totals.get(mailing_id, [0, 0, 0, 0])
        self.totals[mailing_id] = [done + 1, s + success, b + blocked, f + failed]
        done, s, b, f = self.totals[mailing_id]
        return MailingProgressDTO(done_batches=done, success=s, blocked=b, failed=f)

    async def clear(self, *, mailing_id: str) -> None:
        self.cleared.append(mailing_id)


class RecordingNotifications:
    """Запоминает все вызовы NotificationService: (метод, аргумент)."""

    def __init__(self, broadcast_result: MailingResultDTO | None = None) -> None:
        self.calls: list[tuple[str, object]] = []
        self._broadcast_result = broadcast_result or MailingResultDTO(
            success=0, blocked=0, failed=0
        )

    def of(self, method: str) -> list:
        return [arg for name, arg in self.calls if name == method]

    async def send(self, *, chat_id: int, text: str) -> None:
        self.calls.append(("send", (chat_id, text)))

    async def notify_new_booking(self, data) -> None:
        self.calls.append(("notify_new_booking", data))

    async def notify_training_reminder(self, data) -> None:
        self.calls.append(("notify_training_reminder", data))

    async def notify_client_request(self, data) -> None:
        self.calls.append(("notify_client_request", data))

    async def notify_plan_next_training(self, data) -> None:
        self.calls.append(("notify_plan_next_training", data))

    async def notify_subscription(self, data) -> None:
        self.calls.append(("notify_subscription", data))

    async def notify_trainer_digest(self, data) -> None:
        self.calls.append(("notify_trainer_digest", data))

    async def notify_manual_payment_request(self, data) -> None:
        self.calls.append(("notify_manual_payment_request", data))

    async def notify_admins(self, text: str) -> None:
        self.calls.append(("notify_admins", text))

    async def broadcast_copy(self, *, chat_ids, from_chat_id, message_id) -> MailingResultDTO:
        self.calls.append(("broadcast_copy", list(chat_ids)))
        return self._broadcast_result
