from dishka import Provider, provide, Scope

from src.application.mediator import Mediator
from src.application.use_cases.booking.cancel import CancelBookingRequest, CancelBookingUseCase
from src.application.use_cases.booking.confirm import ConfirmBookingRequest, ConfirmBookingUseCase
from src.application.use_cases.booking.create import CreateBookingUseCase, CreateBookingRequest
from src.application.use_cases.calendar.get_available_slots import GetAvailableSlotsRequest, GetAvailableSlotsUseCase
from src.application.use_cases.calendar.get_day_availability_map import GetDayAvailabilityMapRequest, GetDayAvailabilityMapUseCase
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsRequest, GetDaySlotsUseCase
from src.application.use_cases.calendar.get_time_column import GetTimeColumnsUseCase, GetTimeColumnsRequest
from src.application.use_cases.calendar.get_week_grid import GetWeekGridUseCase, GetWeekGridRequest
from src.application.use_cases.calendar.maintain_calendar_buffer import MaintainCalendarBufferUseCase, MaintainCalendarBufferRequest
from src.application.use_cases.calendar.get_slot_by_id import GetSlotByIdUseCase, GetSlotByIdRequest
from src.application.use_cases.client.register import RegisterClientRequest, RegisterClientUseCase
from src.application.use_cases.client.get_by_tg_id import GetClientByTgIdUseCase, GetClientByTgIdRequest
from src.application.use_cases.invite_link.create import CreateTrainerInviteLinkRequest, CreateTrainerInviteLinkUseCase
from src.application.use_cases.invite_link.get_active import GetActiveInviteLinkRequest, GetActiveInviteLinkUseCase
from src.application.use_cases.invite_link.resolve import ResolveInviteLinkRequest, ResolveInviteLinkUseCase
from src.application.use_cases.slot_template.create import CreateSlotTemplateRequest, CreateSlotTemplateUseCase
from src.application.use_cases.slot_template.deactivate import DeactivateSlotTemplateRequest, DeactivateSlotTemplateUseCase
from src.application.use_cases.slot_template.get_active import GetActiveSlotTemplatesRequest, GetActiveSlotTemplatesUseCase
from src.application.use_cases.slot_template.sync_weekday import SyncWeekdaySlotTemplatesRequest, SyncWeekdaySlotTemplatesUseCase
from src.application.use_cases.subscription.get_active import GetActiveSubscriptionRequest, GetActiveSubscriptionUseCase
from src.application.use_cases.subscription.get_active_price_plans import GetActivePricePlansRequest, GetActivePricePlansUseCase
from src.application.use_cases.subscription.purchse import PurchaseSubscriptionRequest, PurchaseSubscriptionUseCase
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdRequest, GetTrainerByIdUseCase
from src.application.use_cases.trainer.get_by_tg_id import GetTrainerByTgIdRequest, GetTrainerByTgIdUseCase
from src.application.use_cases.trainer.get_clients_by_trainer import GetClientsByTrainerRequest, GetClientsByTrainerUseCase
from src.application.use_cases.trainer.get_upcoming_bookings_by_trainer import GetUpcomingBookingsByTrainerRequest, GetUpcomingBookingsByTrainerUseCase
from src.application.use_cases.trainer.register import RegisterTrainerRequest, RegisterTrainerUseCase


class MediatorProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def mediator(
        self,
        maintain_calendar_buffer_use_case: MaintainCalendarBufferUseCase,
        get_day_slots_use_case: GetDaySlotsUseCase,
        get_available_slots_use_case: GetAvailableSlotsUseCase,
        get_week_grid_use_case: GetWeekGridUseCase,
        get_time_column_use_case: GetTimeColumnsUseCase,
        get_day_availability_map_use_case: GetDayAvailabilityMapUseCase,
        get_slot_by_id_use_case: GetSlotByIdUseCase,
        register_client_use_case: RegisterClientUseCase,
        get_client_by_tg_id_use_case: GetClientByTgIdUseCase,
        create_booking_use_case: CreateBookingUseCase,
        get_trainer_by_id_use_case: GetTrainerByIdUseCase,
        resolve_invite_link_use_case: ResolveInviteLinkUseCase,
        confirm_booking_use_case: ConfirmBookingUseCase,
        cancel_booking_use_case: CancelBookingUseCase,
        get_trainer_by_tg_id_use_case: GetTrainerByTgIdUseCase,
        create_slot_template_use_case: CreateSlotTemplateUseCase,
        get_active_slot_template_use_case: GetActiveSlotTemplatesUseCase,
        deactivate_slot_template_use_case: DeactivateSlotTemplateUseCase,
        get_upcoming_booking_by_trainer_use_case: GetUpcomingBookingsByTrainerUseCase,
        get_clients_by_trainer_use_case: GetClientsByTrainerUseCase,
        get_active_invite_link_use_case: GetActiveInviteLinkUseCase,
        purchase_subscription_use_case: PurchaseSubscriptionUseCase,
        get_active_price_plans_use_case: GetActivePricePlansUseCase,
        get_active_subscription_use_case: GetActiveSubscriptionUseCase,
        register_trainer_use_case: RegisterTrainerUseCase,
        create_trainer_invite_link_use_case: CreateTrainerInviteLinkUseCase,
        sync_weekday_slot_tamplate_use_case: SyncWeekdaySlotTemplatesUseCase
    ) -> Mediator:
        mediator = Mediator()

        mediator.register(MaintainCalendarBufferRequest, maintain_calendar_buffer_use_case)
        mediator.register(GetDaySlotsRequest, get_day_slots_use_case)
        mediator.register(GetAvailableSlotsRequest, get_available_slots_use_case)
        mediator.register(GetWeekGridRequest, get_week_grid_use_case)
        mediator.register(GetTimeColumnsRequest, get_time_column_use_case)
        mediator.register(GetDayAvailabilityMapRequest, get_day_availability_map_use_case)
        mediator.register(GetSlotByIdRequest, get_slot_by_id_use_case)
        mediator.register(RegisterClientRequest, register_client_use_case)
        mediator.register(GetClientByTgIdRequest, get_client_by_tg_id_use_case)
        mediator.register(CreateBookingRequest, create_booking_use_case)
        mediator.register(GetTrainerByIdRequest, get_trainer_by_id_use_case)
        mediator.register(ResolveInviteLinkRequest, resolve_invite_link_use_case)
        mediator.register(ConfirmBookingRequest, confirm_booking_use_case)
        mediator.register(CancelBookingRequest, cancel_booking_use_case)
        mediator.register(GetTrainerByTgIdRequest, get_trainer_by_tg_id_use_case)
        mediator.register(CreateSlotTemplateRequest, create_slot_template_use_case)
        mediator.register(GetActiveSlotTemplatesRequest, get_active_slot_template_use_case)
        mediator.register(DeactivateSlotTemplateRequest, deactivate_slot_template_use_case)
        mediator.register(GetUpcomingBookingsByTrainerRequest, get_upcoming_booking_by_trainer_use_case)
        mediator.register(GetClientsByTrainerRequest, get_clients_by_trainer_use_case)
        mediator.register(GetActiveInviteLinkRequest, get_active_invite_link_use_case)
        mediator.register(PurchaseSubscriptionRequest, purchase_subscription_use_case)
        mediator.register(GetActivePricePlansRequest, get_active_price_plans_use_case)
        mediator.register(GetActiveSubscriptionRequest, get_active_subscription_use_case)
        mediator.register(RegisterTrainerRequest, register_trainer_use_case)
        mediator.register(CreateTrainerInviteLinkRequest, create_trainer_invite_link_use_case)
        mediator.register(SyncWeekdaySlotTemplatesRequest, sync_weekday_slot_tamplate_use_case)

        return mediator

