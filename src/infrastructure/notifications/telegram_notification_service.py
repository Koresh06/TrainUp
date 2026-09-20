from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.application.interfaces.notification_service import (
    NotificationService,
    NewBookingNotificationDTO,
    TrainingReminderNotificationDTO,
)
from src.infrastructure.notifications.callback_data.booking import (
    BookingAction,
    BookingActionCD,
)
from src.infrastructure.notifications.callback_data.reminder import ReminderAction, ReminderActionCD


class TelegramNotificationService(NotificationService):
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def send(self, *, chat_id: int, text: str) -> None:
        await self._bot.send_message(chat_id=chat_id, text=text)

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

        full_name = data.client_first_name
        if data.client_last_name:
            full_name += f" {data.client_last_name}"

        username_line = (
            f"@{data.client_username}" if data.client_username else "нет username"
        )

        text = (
            f"📅 Новая запись!\n\n"
            f"👤 Клиент: {full_name} ({username_line})\n"
            f"📞 Телефон: {data.client_phone}\n"
            f"🎂 Возраст: {data.client_age}\n\n"
            f"Дата: {data.date_label}\n"
            f"Время: {data.time_label}\n"
            f"Статус: ожидает подтверждения"
        )
        await self._bot.send_message(
            chat_id=data.chat_id, text=text, reply_markup=kb.as_markup()
        )


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
            f"тренировка с <b>{data.trainer_name}</b>\n\n"
            f"📅 {data.date_label}\n"
            f"🕐 {data.time_label}"
        )
        await self._bot.send_message(
            chat_id=data.chat_id, text=text, reply_markup=kb.as_markup()
        )
    
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