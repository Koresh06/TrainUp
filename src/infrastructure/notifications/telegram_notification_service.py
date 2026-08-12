from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.application.interfaces.notification_service import (
    NotificationService,
    NewBookingNotificationDTO,
)
from src.infrastructure.notifications.booking_callback_data import (
    BookingAction,
    BookingActionCD,
)


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
