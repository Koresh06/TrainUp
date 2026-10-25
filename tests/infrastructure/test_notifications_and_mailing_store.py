from datetime import datetime, timedelta, timezone

import pytest
from aiogram.exceptions import TelegramForbiddenError
from aiogram.methods import SendMessage

from src.application.interfaces.notification_service import (
    NewBookingNotificationDTO,
    SubscriptionEvent,
    SubscriptionNotificationDTO,
)
from src.infrastructure.mailing.redis_progress_store import RedisMailingProgressStore
from src.infrastructure.notifications.telegram_notification_service import (
    TelegramNotificationService,
)


class FakeBot:
    """Подменяет aiogram.Bot: пишет вызовы, chat_id из blocked кидают Forbidden."""

    def __init__(self, blocked: set[int] = frozenset()) -> None:
        self.blocked = blocked
        self.sent: list[dict] = []
        self.copied: list[int] = []

    async def send_message(self, chat_id: int, text: str, reply_markup=None):
        if chat_id in self.blocked:
            raise TelegramForbiddenError(method=SendMessage(chat_id=chat_id, text=text), message="blocked")
        self.sent.append({"chat_id": chat_id, "text": text, "reply_markup": reply_markup})

    async def copy_message(self, chat_id: int, from_chat_id: int, message_id: int):
        if chat_id in self.blocked:
            raise TelegramForbiddenError(method=SendMessage(chat_id=chat_id, text=""), message="blocked")
        self.copied.append(chat_id)


async def test_send_does_not_raise_when_user_blocked_bot() -> None:
    # регресс: падение отправки роняло всю операцию (подтверждение брони и т.п.)
    bot = FakeBot(blocked={42})
    service = TelegramNotificationService(bot=bot)
    await service.send(chat_id=42, text="hi")
    await service.send(chat_id=43, text="hi")
    assert [m["chat_id"] for m in bot.sent] == [43]


async def test_group_unavailable_falls_back_to_trainer_dm() -> None:
    # бота удалили из рабочей группы — уведомление дублируется тренеру в личку
    bot = FakeBot(blocked={-100})
    service = TelegramNotificationService(bot=bot)
    await service.send(chat_id=-100, text="❌ Клиент отменил", fallback_chat_id=7)
    [message] = bot.sent
    assert message["chat_id"] == 7 and "рабочую группу" in message["text"]

    # группа работает — в личку ничего не уходит
    await service.send(chat_id=-200, text="ok", fallback_chat_id=7)
    assert [m["chat_id"] for m in bot.sent] == [7, -200]


async def test_new_booking_fallback_keeps_buttons() -> None:
    bot = FakeBot(blocked={-100})
    await TelegramNotificationService(bot=bot).notify_new_booking(
        NewBookingNotificationDTO(
            chat_id=-100, booking_id=1, date_label="01.11.2026", time_label="10:00",
            client_first_name="Пётр", client_last_name=None, client_username=None,
            client_phone=None, client_age=None, fallback_chat_id=7,
        )
    )
    [message] = bot.sent
    assert message["chat_id"] == 7 and message["reply_markup"] is not None


async def test_broadcast_counts_blocked() -> None:
    bot = FakeBot(blocked={2})
    result = await TelegramNotificationService(bot=bot).broadcast_copy(
        chat_ids=[1, 2, 3], from_chat_id=9, message_id=5, throttle_seconds=0
    )
    assert (result.success, result.blocked, result.failed) == (2, 1, 0)
    assert bot.copied == [1, 3]


@pytest.mark.parametrize(
    "event, hours_left, expected_text, has_button",
    [
        (SubscriptionEvent.WARNING, 47, "через 1 день", True),
        (SubscriptionEvent.WARNING, 2, "через 2 часа", True),
        (SubscriptionEvent.EXPIRED, 0, "Подписка закончилась", True),
        (SubscriptionEvent.GRANTED, 0, "активирована подписка", False),
    ],
)
async def test_subscription_notifications(event, hours_left, expected_text, has_button) -> None:
    bot = FakeBot()
    await TelegramNotificationService(bot=bot).notify_subscription(
        SubscriptionNotificationDTO(
            chat_id=1,
            event=event,
            expired_at=datetime.now(timezone.utc) + timedelta(hours=hours_left),
            hours_left=hours_left,
        )
    )
    [message] = bot.sent
    assert expected_text in message["text"]
    assert (message["reply_markup"] is not None) == has_button


async def test_notify_admins_sends_to_every_admin() -> None:
    bot = FakeBot()
    await TelegramNotificationService(bot=bot).notify_admins("report")
    assert [m["chat_id"] for m in bot.sent] == [777000]  # из tests/conftest.py


async def test_redis_mailing_progress_store() -> None:
    fakeredis = pytest.importorskip("fakeredis")
    store = RedisMailingProgressStore(redis=fakeredis.FakeAsyncRedis())

    first = await store.add_batch_result(mailing_id="m", success=3, blocked=1, failed=0)
    second = await store.add_batch_result(mailing_id="m", success=2, blocked=0, failed=1)

    assert (first.done_batches, second.done_batches) == (1, 2)
    assert (second.success, second.blocked, second.failed) == (5, 1, 1)
    await store.clear(mailing_id="m")
    third = await store.add_batch_result(mailing_id="m", success=0, blocked=0, failed=0)
    assert third.done_batches == 1


async def test_trainer_digest_text() -> None:
    from datetime import date
    from decimal import Decimal

    from src.application.interfaces.notification_service import DigestItemDTO, TrainerDigestDTO

    bot = FakeBot()
    service = TelegramNotificationService(bot=bot)
    await service.notify_trainer_digest(
        TrainerDigestDTO(
            chat_id=1, day=date(2026, 10, 22), day_label="четверг 22 октября", is_tomorrow=False,
            items=[
                DigestItemDTO(time_label="09:00", client_name="Иван <Петров>", is_recurring=True),
                DigestItemDTO(time_label="18:00", client_name="Олег", is_offline=True,
                              is_pending=True, trainer_note="колено"),
            ],
            expected_income=Decimal("6000"), pending_total=1,
        )
    )
    await service.notify_trainer_digest(
        TrainerDigestDTO(chat_id=1, day=date(2026, 10, 23), day_label="пятница 23 октября",
                         is_tomorrow=True, items=[])
    )
    busy, empty = (m["text"] for m in bot.sent)
    assert "Сегодня, четверг 22 октября — 2 тренировки" in busy
    assert "Иван &lt;Петров&gt; 🔁" in busy and "📝 <i>колено</i>" in busy
    assert "последняя в 18:00 · ≈ 6 000 BYN" in busy and "Ждут вашего подтверждения: 1" in busy
    assert "Завтра, пятница 23 октября, тренировок нет" in empty
    assert bot.sent[0]["reply_markup"].inline_keyboard[0][0].callback_data == "digest:2026-10-22"
