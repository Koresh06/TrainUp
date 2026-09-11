from dishka import Provider, provide, Scope

from src.application.mediator import Mediator
from src.application.use_cases.booking.cancel import CancelBookingRequest, CancelBookingUseCase
from src.application.use_cases.booking.confirm import ConfirmBookingRequest, ConfirmBookingUseCase
from src.application.use_cases.booking.count_active_by_slot_ids import CountActiveBookingsBySlotIdsRequest, CountActiveBookingsBySlotIdsUseCase
from src.application.use_cases.booking.create import CreateBookingUseCase, CreateBookingRequest
from src.application.use_cases.booking.get_by_id import GetBookingByIdRequest, GetBookingByIdUseCase
from src.application.use_cases.booking.reschedule import RescheduleBookingRequest, RescheduleBookingUseCase
from src.application.use_cases.booking.send_reminder import SendTrainingReminderRequest, SendTrainingReminderUseCase
from src.application.use_cases.calendar.get_available_slots import GetAvailableSlotsRequest, GetAvailableSlotsUseCase
from src.application.use_cases.calendar.get_day_availability_map import GetDayAvailabilityMapRequest, GetDayAvailabilityMapUseCase
from src.application.use_cases.calendar.get_day_availability_map_assignment import GetDayAvailabilityMapForAssignmentRequest, GetDayAvailabilityMapForAssignmentUseCase
from src.application.use_cases.calendar.get_day_slots import GetDaySlotsRequest, GetDaySlotsUseCase
from src.application.use_cases.calendar.get_time_column import GetTimeColumnsUseCase, GetTimeColumnsRequest
from src.application.use_cases.calendar.get_week_grid import GetWeekGridUseCase, GetWeekGridRequest
from src.application.use_cases.calendar.maintain_calendar_buffer import MaintainCalendarBufferUseCase, MaintainCalendarBufferRequest
from src.application.use_cases.calendar.get_slot_by_id import GetSlotByIdUseCase, GetSlotByIdRequest
from src.application.use_cases.client.get_by_id import GetClientByIdRequest, GetClientByIdUseCase
from src.application.use_cases.recurring_booking.add import AddRecurringBookingRequest, AddRecurringBookingUseCase
from src.application.use_cases.recurring_booking.change import ChangeRecurringBookingScheduleRequest, ChangeRecurringBookingScheduleUseCase
from src.application.use_cases.recurring_booking.deactivate import DeactivateRecurringBookingRequest, DeactivateRecurringBookingUseCase
from src.application.use_cases.recurring_booking.get_all_active_by_trainer import GetActiveRecurringBookingsByTrainerRequest, GetActiveRecurringBookingsByTrainerUseCase
from src.application.use_cases.recurring_booking.get_by_id import GetRecurringBookingByIdRequest, GetRecurringBookingByIdUseCase
from src.application.use_cases.recurring_booking.maintain import MaintainRecurringBookingsRequest, MaintainRecurringBookingsUseCase
from src.application.use_cases.registration_questions.add_custom import AddCustomQuestionRequest, AddCustomQuestionUseCase
from src.application.use_cases.registration_questions.delete import DeleteCustomQuestionRequest, DeleteCustomQuestionUseCase
from src.application.use_cases.registration_questions.get_active import GetActiveRegistrationQuestionsRequest, GetActiveRegistrationQuestionsUseCase
from src.application.use_cases.client.get_clients_by_trainer import GetClientsByTrainerIdRequest, GetClientsByTrainerIdUseCase
from src.application.use_cases.client.register import RegisterClientRequest, RegisterClientUseCase
from src.application.use_cases.client.get_by_tg_id import GetClientByTgIdUseCase, GetClientByTgIdRequest
from src.application.use_cases.invite_link.create import CreateTrainerInviteLinkRequest, CreateTrainerInviteLinkUseCase
from src.application.use_cases.invite_link.get_active import GetActiveInviteLinkRequest, GetActiveInviteLinkUseCase
from src.application.use_cases.invite_link.resolve import ResolveInviteLinkRequest, ResolveInviteLinkUseCase
from src.application.use_cases.registration_questions.get_all import GetAllRegistrationQuestionsRequest, GetAllRegistrationQuestionsUseCase
from src.application.use_cases.registration_questions.update import UpdateQuestionOptionsRequest, UpdateQuestionOptionsUseCase
from src.application.use_cases.registration_questions.get_by_id import GetRegistrationQuestionByIdRequest, GetRegistrationQuestionByIdUseCase
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
from src.application.use_cases.trainer.update import UpdateTrainerProfileRequest, UpdateTrainerProfileUseCase
from src.application.use_cases.trainer_booking_settings.get_by_id import GetTrainerBookingSettingsRequest, GetTrainerBookingSettingsUseCase
from src.application.use_cases.trainer_booking_settings.update import UpdateTrainerBookingSettingsRequest, UpdateTrainerBookingSettingsUseCase
from src.application.use_cases.trainer_pricing_rule.get_by_id import GetTrainerPricingRuleRequest, GetTrainerPricingRuleUseCase
from src.application.use_cases.trainer_pricing_rule.update import UpdateTrainerPricingRuleRequest, UpdateTrainerPricingRuleUseCase


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
        sync_weekday_slot_tamplate_use_case: SyncWeekdaySlotTemplatesUseCase,
        get_trainer_booking_settings_use_case: GetTrainerBookingSettingsUseCase,
        update_trainer_booking_settings_use_case: UpdateTrainerBookingSettingsUseCase,
        count_active_booking_by_slot_ids_use_case: CountActiveBookingsBySlotIdsUseCase,
        get_trainer_pricing_rule_use_case: GetTrainerPricingRuleUseCase,
        update_trainer_pricing_rule_use_case: UpdateTrainerPricingRuleUseCase,
        update_trainer_profile_use_case: UpdateTrainerProfileUseCase,
        get_clients_by_trainer_id_use_case: GetClientsByTrainerIdUseCase,
        send_training_reminder_use_case: SendTrainingReminderUseCase,
        get_active_registration_questions_use_case: GetActiveRegistrationQuestionsUseCase,
        get_all_registration_question_use_case: GetAllRegistrationQuestionsUseCase,
        add_custom_question_use_case: AddCustomQuestionUseCase,
        delete_custom_question_use_case: DeleteCustomQuestionUseCase,
        update_question_options_use_case: UpdateQuestionOptionsUseCase,
        get_registration_question_by_id_use_case: GetRegistrationQuestionByIdUseCase,
        get_client_by_id_use_case: GetClientByIdUseCase,
        get_day_availability_map_for_assignment_use_case: GetDayAvailabilityMapForAssignmentUseCase,
        add_recurring_booking_use_case: AddRecurringBookingUseCase,
        maintain_recurring_booking_use_case: MaintainRecurringBookingsUseCase,
        reschedule_booking_use_case: RescheduleBookingUseCase,
        get_booking_by_id_use_case: GetBookingByIdUseCase,
        change_recurring_booking_schedule_use_case: ChangeRecurringBookingScheduleUseCase,
        deactivate_reccuring_booking_use_case: DeactivateRecurringBookingUseCase,
        get_active_recurring_bookings_by_trainer_use_case: GetActiveRecurringBookingsByTrainerUseCase,
        get_recurring_booking_by_id_use_case: GetRecurringBookingByIdUseCase,

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
        mediator.register(GetTrainerBookingSettingsRequest, get_trainer_booking_settings_use_case)
        mediator.register(UpdateTrainerBookingSettingsRequest, update_trainer_booking_settings_use_case)
        mediator.register(CountActiveBookingsBySlotIdsRequest, count_active_booking_by_slot_ids_use_case)
        mediator.register(GetTrainerPricingRuleRequest, get_trainer_pricing_rule_use_case)
        mediator.register(UpdateTrainerPricingRuleRequest, update_trainer_pricing_rule_use_case)
        mediator.register(UpdateTrainerProfileRequest, update_trainer_profile_use_case)
        mediator.register(GetClientsByTrainerIdRequest, get_clients_by_trainer_id_use_case)
        mediator.register(SendTrainingReminderRequest, send_training_reminder_use_case)
        mediator.register(GetActiveRegistrationQuestionsRequest, get_active_registration_questions_use_case)
        mediator.register(GetAllRegistrationQuestionsRequest, get_all_registration_question_use_case)
        mediator.register(AddCustomQuestionRequest, add_custom_question_use_case)
        mediator.register(DeleteCustomQuestionRequest, delete_custom_question_use_case)
        mediator.register(UpdateQuestionOptionsRequest, update_question_options_use_case)
        mediator.register(GetRegistrationQuestionByIdRequest, get_registration_question_by_id_use_case)
        mediator.register(GetClientByIdRequest, get_client_by_id_use_case)
        mediator.register(GetDayAvailabilityMapForAssignmentRequest, get_day_availability_map_for_assignment_use_case)
        mediator.register(AddRecurringBookingRequest, add_recurring_booking_use_case)
        mediator.register(MaintainRecurringBookingsRequest, maintain_recurring_booking_use_case)
        mediator.register(RescheduleBookingRequest, reschedule_booking_use_case)
        mediator.register(GetBookingByIdRequest, get_booking_by_id_use_case)
        mediator.register(ChangeRecurringBookingScheduleRequest, change_recurring_booking_schedule_use_case)
        mediator.register(DeactivateRecurringBookingRequest, deactivate_reccuring_booking_use_case)
        mediator.register(GetActiveRecurringBookingsByTrainerRequest, get_active_recurring_bookings_by_trainer_use_case)
        mediator.register(GetRecurringBookingByIdRequest, get_recurring_booking_by_id_use_case)

        return mediator

