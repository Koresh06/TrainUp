import asyncio
import logging
from html import escape
from typing import Any

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.application.interfaces.notification_service import (
    AttendanceRequestDTO,
    RatingRequestDTO,
    ClientRequestNotificationDTO,
    MailingResultDTO,
    ManualPaymentRequestDTO,
    NotificationService,
    NewBookingNotificationDTO,
    PlanNextTrainingNotificationDTO,
    SubscriptionEvent,
    SubscriptionNotificationDTO,
    TrainerDigestDTO,
    TrainingReminderNotificationDTO,
)
from src.core.config import settings
from src.domain.enums.request import RequestStatus
from src.infrastructure.notifications.callback_data.booking import (
    BookingAction,
    BookingActionCD,
)
from src.infrastructure.notifications.callback_data.digest import TrainerDigestCD
from src.infrastructure.notifications.callback_data.payment import (
    ManualPaymentAction,
    ManualPaymentCD,
)
from src.infrastructure.notifications.callback_data.plan_next import PlanNextTrainingCD
from src.infrastructure.notifications.callback_data.rating import RateTrainingCD
from src.infrastructure.notifications.callback_data.reminder import ReminderAction, ReminderActionCD
from src.infrastructure.notifications.callback_data.request import RequestActionCD
from src.infrastructure.notifications.callback_data.subscription import (
    RenewSubscriptionCD,
)
from src.utils.timezone import to_moscow

logger = logging.getLogger(__name__)


class TelegramNotificationService(NotificationService):
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def _send(self, chat_id: int | None, text: str, reply_markup: Any = None) -> bool:
        if chat_id is None:
            # страховка: клиент без Telegram — use case'ы такие сообщения
            # не отправляют, но лучше промолчать, чем уронить операцию
            logger.warning("[Notification] skipped: chat_id is None")
            return False
        # пользователь мог заблокировать бота / группа удалена — это не повод
        # ронять бизнес-операцию (подтверждение брони, отмену и т.п.)
        try:
            await self._bot.send_message(
                chat_id=chat_id, text=text, reply_markup=reply_markup
            )
            return True
        except (TelegramForbiddenError, TelegramBadRequest) as error:
            logger.warning("[Notification] chat_id=%s not delivered: %s", chat_id, error)
            return False

    async def send(self, *, chat_id: int | None, text: str) -> None:
        await self._send(chat_id, text)

    async def notify_new_booking(self, data: NewBookingNotificationDTO) -> None:
        kb = InlineKeyboardBuilder()
        kb.button(
            text="✅ Подтвердить",
            callback_data=BookingActionCD(
                action=BookingAction.CONFIRM, booking_id=data.booking_id
            ).pack(),
        )
        kb.button(
            text="❌ Отменить",
            callback_data=BookingActionCD(
                action=BookingAction.CANCEL, booking_id=data.booking_id
            ).pack(),
        )
        kb.adjust(1)

        full_name = escape(data.client_first_name)
        if data.client_last_name:
            full_name += f" {escape(data.client_last_name)}"

        username_line = (
            f"@{data.client_username}" if data.client_username else "нет username"
        )

        text = (
            f"📅 Новая запись!\n\n"
            f"👤 Клиент: {full_name} ({username_line})\n"
            f"📞 Телефон: {data.client_phone or '—'}\n"
            f"🎂 Возраст: {data.client_age or '—'}\n\n"
            f"Дата: {data.date_label}\n"
            f"Время: {data.time_label}\n"
            f"Статус: ожидает подтверждения"
        )
        if data.client_answers:
            answers = "\n".join(
                f"• {escape(label)}: {escape(value)}" for label, value in data.client_answers
            )
            text += f"\n\n📋 Анкета:\n{answers}"

        await self._send(data.chat_id, text, kb.as_markup())


    async def notify_training_reminder(self, data: TrainingReminderNotificationDTO) -> None:
        kb = InlineKeyboardBuilder()
        kb.button(
            text="✅ Подтвердить",
            callback_data=ReminderActionCD(
                action=ReminderAction.CONFIRM, booking_id=data.booking_id
            ).pack(),
        )
        kb.button(
            text="❌ Отменить",
            callback_data=ReminderActionCD(
                action=ReminderAction.CANCEL, booking_id=data.booking_id
            ).pack(),
        )
        kb.adjust(1)
    
        text = (
            f"⏰ <b>Напоминание о тренировке</b>\n\n"
            f"{self.format_time_left(data.minutes_before)} — "
            f"тренировка с <b>{escape(data.trainer_name)}</b>\n\n"
            f"📅 {data.date_label}\n"
            f"🕐 {data.time_label}"
        )
        await self._send(data.chat_id, text, kb.as_markup())
    
    async def notify_client_request(self, data: ClientRequestNotificationDTO) -> None:
        kb = InlineKeyboardBuilder()
        kb.button(
            text="🛠 В работу",
            callback_data=RequestActionCD(
                kind=data.kind,
                request_id=data.request_id,
                status=RequestStatus.IN_PROGRESS,
            ).pack(),
        )
        kb.button(
            text="✅ Закрыть",
            callback_data=RequestActionCD(
                kind=data.kind,
                request_id=data.request_id,
                status=RequestStatus.DONE,
            ).pack(),
        )
        kb.adjust(2)

        username_line = (
            f"@{data.client_username}" if data.client_username else "нет username"
        )
        text = (
            f"📨 <b>Новая заявка: {escape(data.title)}</b>\n\n"
            f"👤 Клиент: {escape(data.client_full_name)} ({username_line})\n"
            f'💬 <a href="tg://user?id={data.client_tg_id}">Написать клиенту</a>\n'
            f"📞 {data.client_phone or '—'}\n\n"
            f"{escape(data.details)}"
        )
        await self._send(data.chat_id, text, kb.as_markup())

    async def notify_plan_next_training(
        self, data: PlanNextTrainingNotificationDTO
    ) -> None:
        kb = InlineKeyboardBuilder()
        kb.button(text="📅 Записаться", callback_data=PlanNextTrainingCD().pack())

        text = (
            f"💪 <b>Пора запланировать следующую тренировку!</b>\n\n"
            f"С прошлого занятия прошло уже {data.days_since_training} "
            f"{self.pluralize_days(data.days_since_training)}. "
            f"Выберите удобное время у тренера <b>{escape(data.trainer_name)}</b> — "
            f"регулярность важнее интенсивности 😉"
        )
        await self._send(data.chat_id, text, kb.as_markup())

    async def notify_subscription(self, data: SubscriptionNotificationDTO) -> None:
        until = to_moscow(data.expired_at).strftime("%d.%m.%Y %H:%M")
        if data.event in (SubscriptionEvent.GRANTED, SubscriptionEvent.PAID):
            title = (
                "✅ <b>Оплата получена — подписка активна</b>"
                if data.event == SubscriptionEvent.PAID
                else "🎁 <b>Вам активирована подписка TrainUp</b>"
            )
            await self._send(
                data.chat_id,
                f"{title}\n\nДействует до {until}.\nКабинет тренера — /trainer",
            )
            return

        kb = InlineKeyboardBuilder()
        kb.button(
            text="💳 Оформить подписку" if data.is_trial else "💳 Продлить подписку",
            callback_data=RenewSubscriptionCD().pack(),
        )
        if data.event == SubscriptionEvent.WARNING:
            left = (
                f"{data.hours_left // 24} {self.pluralize_days(data.hours_left // 24)}"
                if data.hours_left >= 24
                else f"{max(data.hours_left, 1)} {self.pluralize_hours(max(data.hours_left, 1))}"
            )
            if data.is_trial:
                text = (
                    f"⏳ <b>Пробный период заканчивается через {left}</b>\n\n"
                    f"Действует до {until}. Чтобы клиенты и дальше записывались "
                    f"сами, а напоминания и постоянные записи не остановились — "
                    f"оформите подписку. Срок начнётся после пробного периода, "
                    f"ни один день не пропадёт."
                )
            else:
                text = (
                    f"⏳ <b>Подписка заканчивается через {left}</b>\n\n"
                    f"Действует до {until}. После окончания кабинет и запись ваших "
                    f"клиентов будут приостановлены до продления."
                )
        elif data.is_trial:
            text = (
                "⛔ <b>Пробный период закончился</b>\n\n"
                "Кабинет и запись ваших клиентов приостановлены. Расписание, "
                "клиенты и история сохранены — оформите подписку, и всё сразу "
                "заработает как раньше."
            )
        else:
            text = (
                "⛔ <b>Подписка закончилась</b>\n\n"
                "Кабинет тренера и запись ваших клиентов приостановлены. "
                "Продлите подписку, чтобы всё снова заработало."
            )
        await self._send(data.chat_id, text, kb.as_markup())

    async def notify_trainer_digest(self, data: TrainerDigestDTO) -> None:
        kb = InlineKeyboardBuilder()
        kb.button(
            text="📅 Открыть расписание",
            callback_data=TrainerDigestCD(day=data.day.isoformat()).pack(),
        )

        when = "Завтра" if data.is_tomorrow else "Сегодня"
        greeting = "🌙 " if data.is_tomorrow else "☀️ <b>Доброе утро!</b>\n"
        count = len(data.items)
        if not count:
            text = f"{greeting}{when}, {data.day_label}, тренировок нет — свободный день 🙌"
        else:
            lines = []
            for item in data.items:
                line = f"<code>{item.time_label}</code> {escape(item.client_name)}"
                if item.is_recurring:
                    line += " 🔁"
                if item.is_offline:
                    line += " 📵"
                if item.is_pending:
                    line += " ⏳ <i>не подтверждена</i>"
                elif item.client_confirmed:
                    line += " 👍"
                if item.trainer_note:
                    line += f"\n      📝 <i>{escape(item.trainer_note)}</i>"
                lines.append(line)
            footer = f"Первая в {data.items[0].time_label}"
            if count > 1:
                footer += f" · последняя в {data.items[-1].time_label}"
            if data.expected_income:
                amount = f"{data.expected_income:,.0f}".replace(",", " ")
                footer += f" · ≈ {amount} BYN"
            text = (
                f"{greeting}<b>{when}, {data.day_label} — {count} "
                f"{self.pluralize_trainings(count)}</b>\n\n"
                + "\n".join(lines)
                + f"\n\n{footer}"
            )
        if data.pending_total:
            text += f"\n⏳ Ждут вашего подтверждения: {data.pending_total}"
        await self._send(data.chat_id, text, kb.as_markup())

    async def notify_attendance_request(self, data: AttendanceRequestDTO) -> None:
        kb = InlineKeyboardBuilder()
        kb.button(
            text="✅ Приду",
            callback_data=ReminderActionCD(
                action=ReminderAction.CONFIRM, booking_id=data.booking_id
            ).pack(),
        )
        kb.button(
            text="❌ Не смогу",
            callback_data=ReminderActionCD(
                action=ReminderAction.CANCEL, booking_id=data.booking_id
            ).pack(),
        )
        kb.adjust(2)
        when = "Завтра" if data.is_tomorrow else "Сегодня"
        text = (
            f"📅 <b>{when}, {data.day_label}, в {data.time_label}</b> — тренировка "
            f"с <b>{escape(data.trainer_name)}</b>.\n\n"
            f"Подтвердите, пожалуйста, что придёте. Если планы изменились — "
            f"отмените, и время освободится для других."
        )
        await self._send(data.chat_id, text, kb.as_markup())

    async def notify_rating_request(self, data: RatingRequestDTO) -> None:
        kb = InlineKeyboardBuilder()
        for stars in range(1, 6):
            kb.button(
                text=f"{stars}⭐",
                callback_data=RateTrainingCD(booking_id=data.booking_id, stars=stars).pack(),
            )
        kb.adjust(5)
        text = (
            f"🏁 <b>Как прошла тренировка?</b>\n\n"
            f"{data.date_label} с <b>{escape(data.trainer_name)}</b>. "
            f"Оцените от 1 до 5 — тренер увидит оценку и станет ещё лучше 💪"
        )
        await self._send(data.chat_id, text, kb.as_markup())

    async def notify_manual_payment_request(self, data: ManualPaymentRequestDTO) -> None:
        kb = InlineKeyboardBuilder()
        for action, text in (
            (ManualPaymentAction.APPROVE, "✅ Оплата получена"),
            (ManualPaymentAction.REJECT, "❌ Отклонить"),
        ):
            kb.button(
                text=text,
                callback_data=ManualPaymentCD(action=action, external_id=data.external_id).pack(),
            )
        kb.adjust(1)

        text = (
            f"🤝 <b>Заявка на ручную оплату подписки</b>\n\n"
            f"👤 {escape(data.trainer_name)}\n"
            f'💬 <a href="tg://user?id={data.trainer_tg_id}">написать тренеру</a>'
            f" · 📞 {data.trainer_phone or '—'}\n"
            f"📦 {escape(data.plan_label)}\n"
            f"💰 {data.amount_label}\n"
            f"🧾 <code>{data.external_id}</code>\n\n"
            f"Свяжитесь с тренером, примите оплату и нажмите «Оплата получена» — "
            f"подписка активируется автоматически."
        )
        for admin_id in settings.telegram.admin_ids:
            await self._send(admin_id, text, kb.as_markup())

    async def notify_admins(self, text: str) -> None:
        for admin_id in settings.telegram.admin_ids:
            await self._send(admin_id, text)

    async def broadcast_copy(
        self,
        *,
        chat_ids: list[int],
        from_chat_id: int,
        message_id: int,
        throttle_seconds: float = 0.05,
    ) -> MailingResultDTO:
        success = blocked = failed = 0
        for chat_id in chat_ids:
            for attempt in range(2):
                try:
                    await self._bot.copy_message(
                        chat_id=chat_id, from_chat_id=from_chat_id, message_id=message_id
                    )
                    success += 1
                    break
                except TelegramRetryAfter as error:
                    if attempt == 1:
                        failed += 1
                        break
                    logger.warning("[broadcast_copy] flood wait %ss", error.retry_after)
                    await asyncio.sleep(error.retry_after)
                except TelegramForbiddenError:
                    blocked += 1
                    break
                except Exception as error:
                    logger.error("[broadcast_copy] chat_id=%s failed: %s", chat_id, error)
                    failed += 1
                    break
            await asyncio.sleep(throttle_seconds)
        return MailingResultDTO(success=success, blocked=blocked, failed=failed)

    @staticmethod
    def format_time_left(minutes_before: int) -> str:
        if minutes_before < 60:
            minutes = max(minutes_before, 1)
            return f"Через {minutes} {TelegramNotificationService.pluralize_minutes(minutes)}"
    
        hours, minutes = divmod(minutes_before, 60)
        hours_part = f"{hours} {TelegramNotificationService.pluralize_hours(hours)}"
        if minutes == 0:
            return f"Через {hours_part}"
        minutes_part = f"{minutes} {TelegramNotificationService.pluralize_minutes(minutes)}"
        return f"Через {hours_part} {minutes_part}"
    
    @staticmethod
    def pluralize_hours(n: int) -> str:
        if n % 10 == 1 and n % 100 != 11:
            return "час"
        if 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
            return "часа"
        return "часов"
    
    @staticmethod
    def pluralize_minutes(n: int) -> str:
        if n % 10 == 1 and n % 100 != 11:
            return "минуту"
        if 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
            return "минуты"
        return "минут"

    @staticmethod
    def pluralize_trainings(n: int) -> str:
        if n % 10 == 1 and n % 100 != 11:
            return "тренировка"
        if 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
            return "тренировки"
        return "тренировок"

    @staticmethod
    def pluralize_days(n: int) -> str:
        if n % 10 == 1 and n % 100 != 11:
            return "день"
        if 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
            return "дня"
        return "дней"
