from dishka import Provider, provide, Scope

from src.application.use_cases.booking.cancel import CancelBookingUseCase
from src.application.use_cases.booking.confirm import ConfirmBookingUseCase
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.invite_link import TrainerInviteLinkRepository
from src.domain.repositories.slot_template import SlotTemplateRepository
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