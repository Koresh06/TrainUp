from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.application.interfaces.notification_service import MailingResultDTO
from src.application.use_cases.access.get_user_access import (
    GetUserAccessRequest,
    GetUserAccessUseCase,
)
from src.application.use_cases.access.is_trainer_available import (
    IsTrainerAvailableRequest,
    IsTrainerAvailableUseCase,
)
from src.application.use_cases.mailing.enqueue import (
    EnqueueMailingRequest,
    EnqueueMailingUseCase,
)
from src.application.use_cases.mailing.execute import (
    MAILING_BATCH_SIZE,
    ExecuteMailingRequest,
    ExecuteMailingUseCase,
)
from src.application.use_cases.mailing.execute_batch import (
    ExecuteMailingBatchRequest,
    ExecuteMailingBatchUseCase,
)
from src.domain.entities.client import Client
from src.domain.entities.trainer import Trainer
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.mailing import MailingTarget
from src.domain.enums.subscription import SubscriptionPlan, SubscriptionStatus
from src.domain.enums.training import SportExperience
from tests.fakes.common import (
    FakeClients,
    FakeProgressStore,
    FakeSubscriptions,
    FakeTaskQueue,
    FakeTrainers,
    RecordingNotifications,
)


def make_trainer(trainer_id: int, tg_id: int, is_active: bool = True) -> Trainer:
    return Trainer(
        id=trainer_id, tg_id=tg_id, name=f"T{trainer_id}", bio="",
        notification_chat_id=-1, is_active=is_active,
    )


def make_client(client_id: int, tg_id: int, trainer_id: int, is_active: bool = True) -> Client:
    return Client(
        id=client_id, tg_id=tg_id, trainer_id=trainer_id, first_name="C",
        phone="+375", age=30, sport_experience=SportExperience.NONE, is_active=is_active,
    )


def active_subscription(trainer_id: int) -> TrainerSubscription:
    now = datetime.now(timezone.utc)
    return TrainerSubscription(
        trainer_id=trainer_id, plan=SubscriptionPlan.ONE_MONTH, amount=Decimal("30"),
        status=SubscriptionStatus.ACTIVE, started_at=now, expired_at=now + timedelta(days=5),
    )


class TestUserAccess:
    @pytest.fixture
    def use_case(self) -> GetUserAccessUseCase:
        return GetUserAccessUseCase(
            trainer_repo=FakeTrainers(
                [make_trainer(1, 100), make_trainer(2, 200), make_trainer(3, 300, is_active=False)]
            ),
            client_repo=FakeClients(
                [make_client(1, 1001, 1), make_client(2, 1002, 2), make_client(3, 1003, 1, is_active=False)]
            ),
            subscription_repo=FakeSubscriptions([active_subscription(1)]),
        )

    async def test_client_of_trainer_with_subscription(self, use_case) -> None:
        access = await use_case(GetUserAccessRequest(tg_id=1001))
        assert access.client_trainer_available and not access.is_blocked

    async def test_client_of_trainer_without_subscription(self, use_case) -> None:
        access = await use_case(GetUserAccessRequest(tg_id=1002))
        assert not access.client_trainer_available

    async def test_blocked_client_and_trainer(self, use_case) -> None:
        assert (await use_case(GetUserAccessRequest(tg_id=1003))).is_blocked
        assert (await use_case(GetUserAccessRequest(tg_id=300))).is_blocked

    async def test_trainer_subscription_flag(self, use_case) -> None:
        assert (await use_case(GetUserAccessRequest(tg_id=100))).trainer_subscription_active
        assert not (await use_case(GetUserAccessRequest(tg_id=200))).trainer_subscription_active

    async def test_trainer_availability(self) -> None:
        use_case = IsTrainerAvailableUseCase(
            trainer_repo=FakeTrainers([make_trainer(1, 100), make_trainer(3, 300, is_active=False)]),
            subscription_repo=FakeSubscriptions([active_subscription(1), active_subscription(3)]),
        )
        assert await use_case(IsTrainerAvailableRequest(trainer_id=1))
        assert not await use_case(IsTrainerAvailableRequest(trainer_id=3))  # заблокирован
        assert not await use_case(IsTrainerAvailableRequest(trainer_id=99))


class TestMailing:
    def make_execute(self, queue: FakeTaskQueue, notifications=None) -> ExecuteMailingUseCase:
        clients = [make_client(i, 5000 + i, 1 if i % 2 else 2) for i in range(1, 7)]
        clients.append(make_client(7, 5007, 1, is_active=False))
        clients.append(make_client(8, 100, 2))  # тренер 1 ещё и клиент тренера 2
        return ExecuteMailingUseCase(
            trainer_repo=FakeTrainers(
                [make_trainer(1, 100), make_trainer(2, 200), make_trainer(3, 300, is_active=False)]
            ),
            client_repo=FakeClients(clients),
            notification_service=notifications or RecordingNotifications(),
            task_queue=queue,
        )

    @pytest.mark.parametrize(
        "target, expected",
        [
            (MailingTarget.ALL_TRAINERS, 2),
            (MailingTarget.ALL_CLIENTS, 7),
            (MailingTarget.EVERYONE, 8),  # без дублей и без заблокированных
        ],
    )
    async def test_recipients(self, target: MailingTarget, expected: int) -> None:
        queue = FakeTaskQueue()
        count = await self.make_execute(queue)(
            ExecuteMailingRequest(target=target, from_chat_id=1, message_id=2)
        )
        assert count == expected
        [(task, args)] = queue.enqueued
        assert task == "execute_mailing_batch" and len(args[0]) == expected

    async def test_trainer_clients(self) -> None:
        queue = FakeTaskQueue()
        count = await self.make_execute(queue)(
            ExecuteMailingRequest(
                target=MailingTarget.TRAINER_CLIENTS, from_chat_id=1, message_id=2, trainer_id=1
            )
        )
        assert count == 3  # 3 активных клиента тренера 1, заблокированный исключён

    async def test_splits_into_batches(self) -> None:
        queue = FakeTaskQueue()
        use_case = self.make_execute(queue)
        use_case.client_repo = FakeClients(
            [make_client(i, 10_000 + i, 1) for i in range(1, MAILING_BATCH_SIZE + 2)]
        )
        await use_case(
            ExecuteMailingRequest(target=MailingTarget.ALL_CLIENTS, from_chat_id=1, message_id=2)
        )
        assert [len(args[0]) for _, args in queue.enqueued] == [MAILING_BATCH_SIZE, 1]

    async def test_no_recipients_reports_to_admins(self) -> None:
        notifications = RecordingNotifications()
        use_case = self.make_execute(FakeTaskQueue(), notifications)
        use_case.client_repo = FakeClients()
        await use_case(
            ExecuteMailingRequest(target=MailingTarget.ALL_CLIENTS, from_chat_id=1, message_id=2)
        )
        assert "получателей нет" in notifications.of("notify_admins")[0]

    async def test_report_after_last_batch(self) -> None:
        notifications = RecordingNotifications(MailingResultDTO(success=2, blocked=1, failed=0))
        store = FakeProgressStore()
        use_case = ExecuteMailingBatchUseCase(notification_service=notifications, progress_store=store)
        request = dict(from_chat_id=1, message_id=2, total_batches=2, target_label="X", mailing_id="m1")

        await use_case(ExecuteMailingBatchRequest(chat_ids=[1, 2, 3], **request))
        assert notifications.of("notify_admins") == []
        await use_case(ExecuteMailingBatchRequest(chat_ids=[4, 5, 6], **request))

        [report] = notifications.of("notify_admins")
        assert "Доставлено: <b>4</b>" in report and "бота: <b>2</b>" in report
        assert store.cleared == ["m1"]

    async def test_enqueue_requires_trainer_for_trainer_clients(self) -> None:
        with pytest.raises(ValueError):
            await EnqueueMailingUseCase(task_queue=FakeTaskQueue())(
                EnqueueMailingRequest(
                    target=MailingTarget.TRAINER_CLIENTS, from_chat_id=1, message_id=2
                )
            )
