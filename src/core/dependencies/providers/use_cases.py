from dishka import Provider, provide, Scope

from src.application.use_cases.booking.cancel import CancelBookingUseCase
from src.application.use_cases.booking.confirm import ConfirmBookingUseCase
from src.application.use_cases.invite_link.create import CreateTrainerInviteLinkUseCase
from src.application.use_cases.invite_link.get_active import GetActiveInviteLinkUseCase
from src.application.use_cases.slot_template.create import CreateSlotTemplateUseCase
from src.application.use_cases.slot_template.deactivate import (
    DeactivateSlotTemplateUseCase,
)
from src.application.use_cases.slot_template.get_active import (
    GetActiveSlotTemplatesUseCase,
)
from src.application.use_cases.slot_template.sync_weekday import SyncWeekdaySlotTemplatesUseCase
from src.application.use_cases.subscription.get_active import GetActiveSubscriptionUseCase
from src.application.use_cases.subscription.get_active_price_plans import GetActivePricePlansUseCase
from src.application.use_cases.subscription.purchse import PurchaseSubscriptionUseCase
from src.application.use_cases.trainer.get_by_tg_id import GetTrainerByTgIdUseCase
from src.application.use_cases.trainer.get_clients_by_trainer import (
    GetClientsByTrainerUseCase,
)
from src.application.use_cases.trainer.get_upcoming_bookings_by_trainer import (
    GetUpcomingBookingsByTrainerUseCase,
)
from src.application.use_cases.trainer.register import RegisterTrainerUseCase
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.invite_link import TrainerInviteLinkRepository
from src.domain.repositories.slot_template import SlotTemplateRepository
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.subscription_price_plan import SubscriptionPricePlanRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.services.calendar_service import CalendarService

from src.application.use_cases.booking.create import CreateBookingUseCase
from src.application.use_cases.calendar.get_available_slots import (
    GetAvailableSlotsUseCase,
)
from src.application.use_cases.calendar.get_day_availability_map import (
    GetDayAvailabilityMapUseCase,
)
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsUseCase
from src.application.use_cases.calendar.get_time_column import GetTimeColumnsUseCase
from src.application.use_cases.calendar.get_week_grid import GetWeekGridUseCase
from src.application.use_cases.calendar.maintain_calendar_buffer import (
    MaintainCalendarBufferUseCase,
)
from src.application.use_cases.calendar.get_slot_by_id import GetSlotByIdUseCase
from src.application.use_cases.client.register import RegisterClientUseCase
from src.application.use_cases.client.get_by_tg_id import GetClientByTgIdUseCase
from src.application.use_cases.invite_link.resolve import ResolveInviteLinkUseCase
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdUseCase
from src.application.interfaces.notification_service import NotificationService

from src.infrastructure.database.transaction_manager.base import TransactionManager


class UseCasesProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def maintain_calendar_buffer_use_case(
        self,
        calendar_service: CalendarService,
        trainer_repo: TrainerRepository,
        transaction_manager: TransactionManager,
    ) -> MaintainCalendarBufferUseCase:
        return MaintainCalendarBufferUseCase(
            calendar_service=calendar_service,
            trainer_repo=trainer_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_day_slots_use_case(
        self, calendar_service: CalendarService
    ) -> GetDaySlotsUseCase:
        return GetDaySlotsUseCase(calendar_service=calendar_service)

    @provide
    def get_available_slots_use_case(
        self, calendar_service: CalendarService
    ) -> GetAvailableSlotsUseCase:
        return GetAvailableSlotsUseCase(calendar_service=calendar_service)

    @provide
    def get_week_grid_use_case(
        self,
        calendar_service: CalendarService,
    ) -> GetWeekGridUseCase:
        return GetWeekGridUseCase(calendar_service=calendar_service)

    @provide
    def get_time_column_use_case(
        self,
        template_repo: SlotTemplateRepository,
    ) -> GetTimeColumnsUseCase:
        return GetTimeColumnsUseCase(template_repo=template_repo)

    @provide
    def get_day_availability_map_use_case(
        self, calendar_service: CalendarService
    ) -> GetDayAvailabilityMapUseCase:
        return GetDayAvailabilityMapUseCase(calendar_service=calendar_service)

    @provide
    def get_slot_by_id_use_case(
        self, slot_repo: CalendarSlotRepository
    ) -> GetSlotByIdUseCase:
        return GetSlotByIdUseCase(slot_repo=slot_repo)

    @provide
    def register_client_use_case(
        self, client_repo: ClientRepository, transaction_manager: TransactionManager
    ) -> RegisterClientUseCase:
        return RegisterClientUseCase(
            client_repo=client_repo, transaction_manager=transaction_manager
        )

    @provide
    def get_client_by_tg_id_use_case(
        self, client_repo: ClientRepository
    ) -> GetClientByTgIdUseCase:
        return GetClientByTgIdUseCase(client_repo=client_repo)

    @provide
    def create_booking_use_case(
        self,
        calendar_service: CalendarService,
        booking_repo: BookingRepository,
        trainer_repo: TrainerRepository,
        client_repo: ClientRepository,
        notification_service: NotificationService,
        transaction_manager: TransactionManager,
    ) -> CreateBookingUseCase:
        return CreateBookingUseCase(
            calendar_service=calendar_service,
            booking_repo=booking_repo,
            trainer_repo=trainer_repo,
            client_repo=client_repo,
            notification_service=notification_service,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_trainer_by_id_use_case(
        self,
        trainer_repo: TrainerRepository,
    ) -> GetTrainerByIdUseCase:
        return GetTrainerByIdUseCase(
            trainer_repo=trainer_repo,
        )

    @provide
    def resolve_invite_link_use_case(
        self,
        invite_link_repo: TrainerInviteLinkRepository,
    ) -> ResolveInviteLinkUseCase:
        return ResolveInviteLinkUseCase(
            invite_link_repo=invite_link_repo,
        )

    @provide
    def confirm_booking_use_case(
        self,
        booking_repo: BookingRepository,
        client_repo: ClientRepository,
        notification_service: NotificationService,
        transaction_manager: TransactionManager,
    ) -> ConfirmBookingUseCase:
        return ConfirmBookingUseCase(
            booking_repo=booking_repo,
            client_repo=client_repo,
            notification_service=notification_service,
            transaction_manager=transaction_manager,
        )

    @provide
    def cancel_booking_use_case(
        self,
        booking_repo: BookingRepository,
        client_repo: ClientRepository,
        calendar_service: CalendarService,
        notification_service: NotificationService,
        transaction_manager: TransactionManager,
    ) -> CancelBookingUseCase:
        return CancelBookingUseCase(
            booking_repo=booking_repo,
            client_repo=client_repo,
            calendar_service=calendar_service,
            notification_service=notification_service,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_trainer_by_tg_id_use_case(
        self,
        trainer_repo: TrainerRepository,
    ) -> GetTrainerByTgIdUseCase:
        return GetTrainerByTgIdUseCase(
            trainer_repo=trainer_repo,
        )

    @provide
    def create_slot_template_use_case(
        self,
        template_repo: SlotTemplateRepository,
        transaction_manager: TransactionManager,
    ) -> CreateSlotTemplateUseCase:
        return CreateSlotTemplateUseCase(
            template_repo=template_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_active_slot_template_use_case(
        self,
        template_repo: SlotTemplateRepository,
    ) -> GetActiveSlotTemplatesUseCase:
        return GetActiveSlotTemplatesUseCase(
            template_repo=template_repo,
        )

    @provide
    def deactivate_slot_template_use_case(
        self,
        template_repo: SlotTemplateRepository,
        transaction_manager: TransactionManager,
    ) -> DeactivateSlotTemplateUseCase:
        return DeactivateSlotTemplateUseCase(
            template_repo=template_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_upcoming_booking_by_trainer_use_case(
        self,
        booking_repo: BookingRepository,
    ) -> GetUpcomingBookingsByTrainerUseCase:
        return GetUpcomingBookingsByTrainerUseCase(
            booking_repo=booking_repo,
        )

    @provide
    def get_clients_by_trainer_use_case(
        self,
        client_repo: ClientRepository,
    ) -> GetClientsByTrainerUseCase:
        return GetClientsByTrainerUseCase(
            client_repo=client_repo,
        )

    @provide
    def get_active_invite_link_use_case(
        self,
        invite_link_repo: TrainerInviteLinkRepository,
    ) -> GetActiveInviteLinkUseCase:
        return GetActiveInviteLinkUseCase(
            invite_link_repo=invite_link_repo,
        )

    @provide
    def purchase_subscription_use_case(
        self,
        price_plan_repo: SubscriptionPricePlanRepository,
        subscription_repo: TrainerSubscriptionRepository,
        transaction_manager: TransactionManager,
    ) -> PurchaseSubscriptionUseCase:
        return PurchaseSubscriptionUseCase(
            price_plan_repo=price_plan_repo,
            subscription_repo=subscription_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_active_price_plans_use_case(
        self,
        price_plan_repo: SubscriptionPricePlanRepository,
    ) -> GetActivePricePlansUseCase:
        return GetActivePricePlansUseCase(
            price_plan_repo=price_plan_repo,
        )

    @provide
    def get_active_subscription_use_case(
        self,
        subscription_repo: TrainerSubscriptionRepository,
    ) -> GetActiveSubscriptionUseCase:
        return GetActiveSubscriptionUseCase(
            subscription_repo=subscription_repo,
        )

    @provide
    def register_trainer_use_case(
        self,
        trainer_repo: TrainerRepository,
        invite_link_repo: TrainerInviteLinkRepository,
        transaction_manager: TransactionManager,
    ) -> RegisterTrainerUseCase:
        return RegisterTrainerUseCase(
            trainer_repo=trainer_repo,
            invite_link_repo=invite_link_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def create_trainer_invite_link_use_case(
        self,
        invite_link_repo: TrainerInviteLinkRepository,
        transaction_manager: TransactionManager,
    ) -> CreateTrainerInviteLinkUseCase:
        return CreateTrainerInviteLinkUseCase(
            invite_link_repo=invite_link_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def sync_weekday_slot_tamplate_use_case(
        self,
        template_repo: SlotTemplateRepository,
        slot_repo: CalendarSlotRepository,
        calendar_service: CalendarService,
        transaction_manager: TransactionManager,
    ) -> SyncWeekdaySlotTemplatesUseCase:
        return SyncWeekdaySlotTemplatesUseCase(
            template_repo=template_repo,
            slot_repo=slot_repo,
            calendar_service=calendar_service,
            transaction_manager=transaction_manager,
        )