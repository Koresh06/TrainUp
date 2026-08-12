from aiogram import Bot
from dishka import Provider, Scope, provide

from src.application.interfaces.notification_service import NotificationService
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.slot_template import SlotTemplateRepository
from src.domain.services.calendar_service import CalendarService
from src.infrastructure.notifications.telegram_notification_service import TelegramNotificationService


class ServicesProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_calendar_service(
        self,
        slot_repo: CalendarSlotRepository,
        template_repo: SlotTemplateRepository,
    ) -> CalendarService:
        return CalendarService(
            slot_repo=slot_repo,
            template_repo=template_repo,
        )

    @provide(scope=Scope.REQUEST)
    def get_notification_service(
        self,
        bot: Bot,
    ) -> NotificationService:
        return TelegramNotificationService(bot=bot)