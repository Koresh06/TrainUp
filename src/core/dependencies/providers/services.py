import logging

from aiogram import Bot
from redis.asyncio import Redis
from dishka import Provider, Scope, provide

from src.application.interfaces.mailing_progress import MailingProgressStore
from src.application.services.package_charge import PackageChargeService
from src.application.services.referral_reward import ReferralRewardService
from src.application.services.trainer_referral_reward import TrainerReferralRewardService
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.application.services.payment_provider_registry import PaymentProviderRegistry
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.client_package import ClientPackageRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.repositories.trainer_booking_settings import TrainerBookingSettingsRepository
from src.domain.repositories.trainer_vacation import TrainerVacationRepository
from src.core.config import settings
from src.infrastructure.payment.providers.manual import ManualPaymentProvider
from src.infrastructure.payment.providers.telegram_stars import TelegramStarsProvider
from src.infrastructure.payment.providers.test import TestPaymentProvider
from src.infrastructure.payment.providers.yookassa import YooKassaProvider
from src.application.interfaces.notification_service import NotificationService
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.slot_template import SlotTemplateRepository
from src.domain.services.calendar_service import CalendarService
from src.infrastructure.mailing.redis_progress_store import RedisMailingProgressStore
from src.infrastructure.notifications.telegram_notification_service import TelegramNotificationService


logger = logging.getLogger(__name__)


class ServicesProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_trainer_referral_reward_service(
        self,
        trainer_repo: TrainerRepository,
        subscription_repo: TrainerSubscriptionRepository,
        notification_service: NotificationService,
    ) -> TrainerReferralRewardService:
        return TrainerReferralRewardService(
            trainer_repo=trainer_repo,
            subscription_repo=subscription_repo,
            notification_service=notification_service,
        )

    @provide(scope=Scope.REQUEST)
    def get_referral_reward_service(
        self,
        client_repo: ClientRepository,
        package_repo: ClientPackageRepository,
        booking_settings_repo: TrainerBookingSettingsRepository,
        notification_service: NotificationService,
    ) -> ReferralRewardService:
        return ReferralRewardService(
            client_repo=client_repo,
            package_repo=package_repo,
            booking_settings_repo=booking_settings_repo,
            notification_service=notification_service,
        )

    @provide(scope=Scope.REQUEST)
    def get_package_charge_service(
        self,
        package_repo: ClientPackageRepository,
        booking_settings_repo: TrainerBookingSettingsRepository,
        client_repo: ClientRepository,
        trainer_repo: TrainerRepository,
        notification_service: NotificationService,
    ) -> PackageChargeService:
        return PackageChargeService(
            package_repo=package_repo,
            booking_settings_repo=booking_settings_repo,
            client_repo=client_repo,
            trainer_repo=trainer_repo,
            notification_service=notification_service,
        )

    @provide(scope=Scope.REQUEST)
    def get_calendar_service(
        self,
        slot_repo: CalendarSlotRepository,
        template_repo: SlotTemplateRepository,
        booking_repo: BookingRepository,
        vacation_repo: TrainerVacationRepository,
    ) -> CalendarService:
        return CalendarService(
            slot_repo=slot_repo,
            template_repo=template_repo,
            booking_repo=booking_repo,
            vacation_repo=vacation_repo,
        )

    @provide(scope=Scope.REQUEST)
    def get_notification_service(
        self,
        bot: Bot,
    ) -> NotificationService:
        return TelegramNotificationService(bot=bot)

    @provide(scope=Scope.REQUEST)
    def get_mailing_progress_store(self, redis: Redis) -> MailingProgressStore:
        return RedisMailingProgressStore(redis=redis)

    @provide(scope=Scope.APP)
    def get_payment_provider_registry(self, bot: Bot) -> PaymentProviderRegistry:
        """Стратегии оплаты: подключаются флагами APP_CONFIG__PAYMENT__*__ENABLED.
        Новый способ — новый PaymentProvider и одна строка регистрации здесь."""
        payment = settings.payment
        registry = PaymentProviderRegistry()
        if payment.yookassa.enabled:
            registry.register(YooKassaProvider(settings=payment.yookassa))
        if payment.telegram_stars.enabled:
            registry.register(TelegramStarsProvider(bot=bot, settings=payment.telegram_stars))
        if payment.manual.enabled:
            registry.register(ManualPaymentProvider(settings=payment.manual))
        if payment.test_mode:
            registry.register(TestPaymentProvider())
        # настройки читаются при старте процесса: после правки .env бот, worker
        # и webhook нужно перезапустить — по этой строке видно, что подхватилось
        logger.info(
            "[Payments] enabled methods: %s",
            ", ".join(m.value for m in registry.available_methods()) or "none",
        )
        return registry
