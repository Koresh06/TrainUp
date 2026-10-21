from dishka import Provider, provide, Scope

from src.application.mediator import Mediator
from src.application.use_cases.admin.get_analytics import (
    GetAdminAnalyticsRequest,
    GetAdminAnalyticsUseCase,
)
from src.application.use_cases.bot_user.set_bot_blocked import (
    SetBotBlockedByUserRequest,
    SetBotBlockedByUserUseCase,
)
from src.application.use_cases.bot_user.track_activity import (
    TrackUserActivityRequest,
    TrackUserActivityUseCase,
)
from src.application.use_cases.booking.cancel import (
    CancelBookingRequest,
    CancelBookingUseCase,
)
from src.application.use_cases.booking.confirm import (
    ConfirmBookingRequest,
    ConfirmBookingUseCase,
)
from src.application.use_cases.booking.count_active_by_slot_ids import (
    CountActiveBookingsBySlotIdsRequest,
    CountActiveBookingsBySlotIdsUseCase,
)
from src.application.use_cases.booking.create import (
    CreateBookingUseCase,
    CreateBookingRequest,
)
from src.application.use_cases.booking.get_by_id import (
    GetBookingByIdRequest,
    GetBookingByIdUseCase,
)
from src.application.use_cases.booking.mark_completed import MarkBookingCompletedRequest, MarkBookingCompletedUseCase
from src.application.use_cases.booking.reschedule import (
    RescheduleBookingRequest,
    RescheduleBookingUseCase,
)
from src.application.use_cases.booking.send_reminder import (
    SendTrainingReminderRequest,
    SendTrainingReminderUseCase,
)
from src.application.use_cases.calendar.get_available_slots import (
    GetAvailableSlotsRequest,
    GetAvailableSlotsUseCase,
)
from src.application.use_cases.calendar.get_day_availability_map import (
    GetDayAvailabilityMapRequest,
    GetDayAvailabilityMapUseCase,
)
from src.application.use_cases.calendar.get_day_availability_map_assignment import (
    GetDayAvailabilityMapForAssignmentRequest,
    GetDayAvailabilityMapForAssignmentUseCase,
)
from src.application.use_cases.calendar.get_day_slots import (
    GetDaySlotsRequest,
    GetDaySlotsUseCase,
)
from src.application.use_cases.calendar.get_time_column import (
    GetTimeColumnsUseCase,
    GetTimeColumnsRequest,
)
from src.application.use_cases.calendar.get_week_grid import (
    GetWeekGridUseCase,
    GetWeekGridRequest,
)
from src.application.use_cases.calendar.maintain_calendar_buffer import (
    MaintainCalendarBufferUseCase,
    MaintainCalendarBufferRequest,
)
from src.application.use_cases.calendar.get_slot_by_id import (
    GetSlotByIdUseCase,
    GetSlotByIdRequest,
)
from src.application.use_cases.client.get_answers_by_id import GetClientAnswersRequest, GetClientAnswersUseCase
from src.application.use_cases.client.get_by_id import (
    GetClientByIdRequest,
    GetClientByIdUseCase,
)
from src.application.use_cases.recurring_booking.add import (
    AddRecurringBookingRequest,
    AddRecurringBookingUseCase,
)
from src.application.use_cases.recurring_booking.change import (
    ChangeRecurringBookingScheduleRequest,
    ChangeRecurringBookingScheduleUseCase,
)
from src.application.use_cases.recurring_booking.deactivate import (
    DeactivateRecurringBookingRequest,
    DeactivateRecurringBookingUseCase,
)
from src.application.use_cases.recurring_booking.get_active_by_client import GetActiveRecurringBookingsByClientRequest, GetActiveRecurringBookingsByClientUseCase
from src.application.use_cases.recurring_booking.get_all_active_by_trainer import (
    GetActiveRecurringBookingsByTrainerRequest,
    GetActiveRecurringBookingsByTrainerUseCase,
)
from src.application.use_cases.recurring_booking.get_by_id import (
    GetRecurringBookingByIdRequest,
    GetRecurringBookingByIdUseCase,
)
from src.application.use_cases.recurring_booking.maintain import (
    MaintainRecurringBookingsRequest,
    MaintainRecurringBookingsUseCase,
)
from src.application.use_cases.registration_questions.add_custom import (
    AddCustomQuestionRequest,
    AddCustomQuestionUseCase,
)
from src.application.use_cases.registration_questions.delete import (
    DeleteCustomQuestionRequest,
    DeleteCustomQuestionUseCase,
)
from src.application.use_cases.registration_questions.get_active import (
    GetActiveRegistrationQuestionsRequest,
    GetActiveRegistrationQuestionsUseCase,
)
from src.application.use_cases.client.get_clients_by_trainer import (
    GetClientsByTrainerIdRequest,
    GetClientsByTrainerIdUseCase,
)
from src.application.use_cases.client.register import (
    RegisterClientRequest,
    RegisterClientUseCase,
)
from src.application.use_cases.client.get_by_tg_id import (
    GetClientByTgIdUseCase,
    GetClientByTgIdRequest,
)
from src.application.use_cases.invite_link.create import (
    CreateTrainerInviteLinkRequest,
    CreateTrainerInviteLinkUseCase,
)
from src.application.use_cases.invite_link.get_active import (
    GetActiveInviteLinkRequest,
    GetActiveInviteLinkUseCase,
)
from src.application.use_cases.invite_link.resolve import (
    ResolveInviteLinkRequest,
    ResolveInviteLinkUseCase,
)
from src.application.use_cases.registration_questions.get_all import (
    GetAllRegistrationQuestionsRequest,
    GetAllRegistrationQuestionsUseCase,
)
from src.application.use_cases.registration_questions.update import (
    UpdateQuestionOptionsRequest,
    UpdateQuestionOptionsUseCase,
)
from src.application.use_cases.registration_questions.get_by_id import (
    GetRegistrationQuestionByIdRequest,
    GetRegistrationQuestionByIdUseCase,
)
from src.application.use_cases.slot_template.create import (
    CreateSlotTemplateRequest,
    CreateSlotTemplateUseCase,
)
from src.application.use_cases.slot_template.deactivate import (
    DeactivateSlotTemplateRequest,
    DeactivateSlotTemplateUseCase,
)
from src.application.use_cases.slot_template.get_active import (
    GetActiveSlotTemplatesRequest,
    GetActiveSlotTemplatesUseCase,
)
from src.application.use_cases.slot_template.sync_weekday import (
    SyncWeekdaySlotTemplatesRequest,
    SyncWeekdaySlotTemplatesUseCase,
)
from src.application.use_cases.stats.get_trainer import (
    GetTrainerStatsRequest,
    GetTrainerStatsUseCase,
)
from src.application.use_cases.subscription.get_active import (
    GetActiveSubscriptionRequest,
    GetActiveSubscriptionUseCase,
)
from src.application.use_cases.subscription.get_active_price_plans import (
    GetActivePricePlansRequest,
    GetActivePricePlansUseCase,
)
from src.application.use_cases.trainer.get_by_id import (
    GetTrainerByIdRequest,
    GetTrainerByIdUseCase,
)
from src.application.use_cases.trainer.get_by_tg_id import (
    GetTrainerByTgIdRequest,
    GetTrainerByTgIdUseCase,
)
from src.application.use_cases.trainer.get_clients_by_trainer import (
    GetClientsByTrainerRequest,
    GetClientsByTrainerUseCase,
)
from src.application.use_cases.trainer.register import (
    RegisterTrainerRequest,
    RegisterTrainerUseCase,
)
from src.application.use_cases.trainer.update import (
    UpdateTrainerProfileRequest,
    UpdateTrainerProfileUseCase,
)
from src.application.use_cases.trainer_booking_settings.get_by_id import (
    GetTrainerBookingSettingsRequest,
    GetTrainerBookingSettingsUseCase,
)
from src.application.use_cases.trainer_booking_settings.update import (
    UpdateTrainerBookingSettingsRequest,
    UpdateTrainerBookingSettingsUseCase,
)
from src.application.use_cases.trainer_pricing_rule.get_by_id import (
    GetTrainerPricingRuleRequest,
    GetTrainerPricingRuleUseCase,
)
from src.application.use_cases.trainer_pricing_rule.update import (
    UpdateTrainerPricingRuleRequest,
    UpdateTrainerPricingRuleUseCase,
)
from src.application.use_cases.booking.mark_past_completed import (
    MarkPastBookingsCompletedUseCase,
    MarkPastBookingsCompletedRequest,
)
from src.application.use_cases.trainer_reminder_settings.get_by_trainer_id import GetTrainerReminderSettingsRequest, GetTrainerReminderSettingsUseCase
from src.application.use_cases.trainer_reminder_settings.update import UpdateTrainerReminderSettingsRequest, UpdateTrainerReminderSettingsUseCase

from src.application.use_cases.client_request.create_program import (
    CreateProgramRequestRequest,
    CreateProgramRequestUseCase,
)
from src.application.use_cases.client_request.create_consultation import (
    CreateConsultationRequestRequest,
    CreateConsultationRequestUseCase,
)
from src.application.use_cases.client_request.create_feedback import (
    CreateFeedbackRequest,
    CreateFeedbackUseCase,
)
from src.application.use_cases.client_request.get_by_trainer import (
    GetClientRequestsByTrainerRequest,
    GetClientRequestsByTrainerUseCase,
)
from src.application.use_cases.client_request.get_by_id import (
    GetClientRequestByIdRequest,
    GetClientRequestByIdUseCase,
)
from src.application.use_cases.client_request.update_status import (
    UpdateClientRequestStatusRequest,
    UpdateClientRequestStatusUseCase,
)
from src.application.use_cases.faq.get_active import (
    GetActiveFaqItemsRequest,
    GetActiveFaqItemsUseCase,
)
from src.application.use_cases.faq.get_by_id import (
    GetFaqItemByIdRequest,
    GetFaqItemByIdUseCase,
)
from src.application.use_cases.faq.add import (
    AddFaqItemRequest,
    AddFaqItemUseCase,
)
from src.application.use_cases.faq.deactivate import (
    DeactivateFaqItemRequest,
    DeactivateFaqItemUseCase,
)
from src.application.use_cases.calendar.set_slot_blocked import (
    SetSlotBlockedRequest,
    SetSlotBlockedUseCase,
)
from src.application.use_cases.calendar.set_day_blocked import (
    SetDayBlockedRequest,
    SetDayBlockedUseCase,
)
from src.application.use_cases.booking.get_upcoming_by_client import (
    GetUpcomingBookingsByClientRequest,
    GetUpcomingBookingsByClientUseCase,
)
from src.application.use_cases.client.update_answers import (
    UpdateClientAnswersRequest,
    UpdateClientAnswersUseCase,
)
from src.application.use_cases.booking.send_plan_next_reminder import (
    SendPlanNextTrainingReminderRequest,
    SendPlanNextTrainingReminderUseCase,
)

from src.application.use_cases.subscription.grant import (
    GrantSubscriptionRequest,
    GrantSubscriptionUseCase,
)
from src.application.use_cases.subscription.check_expiring import (
    CheckExpiringSubscriptionsRequest,
    CheckExpiringSubscriptionsUseCase,
)
from src.application.use_cases.subscription.get_by_trainer import (
    GetSubscriptionsByTrainerRequest,
    GetSubscriptionsByTrainerUseCase,
)
from src.application.use_cases.access.get_user_access import (
    GetUserAccessRequest,
    GetUserAccessUseCase,
)
from src.application.use_cases.trainer.set_blocked import (
    SetTrainerBlockedRequest,
    SetTrainerBlockedUseCase,
)
from src.application.use_cases.client.set_blocked import (
    SetClientBlockedRequest,
    SetClientBlockedUseCase,
)
from src.application.use_cases.client.search import (
    SearchClientsRequest,
    SearchClientsUseCase,
)
from src.application.use_cases.trainer.get_all import (
    GetAllTrainersRequest,
    GetAllTrainersUseCase,
)
from src.application.use_cases.admin.get_overview_stats import (
    GetAdminOverviewStatsRequest,
    GetAdminOverviewStatsUseCase,
)
from src.application.use_cases.admin.get_trainer_report import (
    GetAdminTrainerReportRequest,
    GetAdminTrainerReportUseCase,
)
from src.application.use_cases.admin.export_report import (
    ExportReportRequest,
    ExportReportUseCase,
)
from src.application.use_cases.mailing.enqueue import (
    EnqueueMailingRequest,
    EnqueueMailingUseCase,
)
from src.application.use_cases.mailing.execute import (
    ExecuteMailingRequest,
    ExecuteMailingUseCase,
)
from src.application.use_cases.mailing.execute_batch import (
    ExecuteMailingBatchRequest,
    ExecuteMailingBatchUseCase,
)

from src.application.use_cases.access.is_trainer_available import (
    IsTrainerAvailableRequest,
    IsTrainerAvailableUseCase,
)

from src.application.use_cases.payment.create_subscription_payment import (
    CreateSubscriptionPaymentRequest,
    CreateSubscriptionPaymentUseCase,
)
from src.application.use_cases.payment.confirm import (
    ConfirmPaymentRequest,
    ConfirmPaymentUseCase,
)
from src.application.use_cases.payment.reject import (
    RejectPaymentRequest,
    RejectPaymentUseCase,
)
from src.application.use_cases.payment.get_methods import (
    GetPaymentMethodsRequest,
    GetPaymentMethodsUseCase,
)
from src.application.use_cases.payment.get_by_external_id import (
    GetPaymentByExternalIdRequest,
    GetPaymentByExternalIdUseCase,
)

from src.application.use_cases.client.create_offline import CreateOfflineClientRequest, CreateOfflineClientUseCase

from src.application.use_cases.client.update_by_trainer import UpdateClientFieldRequest, UpdateClientFieldUseCase

from src.application.use_cases.client.delete_offline import DeleteOfflineClientRequest, DeleteOfflineClientUseCase

from src.application.use_cases.client.claim_invite import ClaimClientInviteRequest, ClaimClientInviteUseCase

from src.application.use_cases.client.get_by_invite_token import GetClientByInviteTokenRequest, GetClientByInviteTokenUseCase

from src.application.use_cases.booking.get_views import GetBookingViewsRequest, GetBookingViewsUseCase

from src.application.use_cases.booking.create_by_trainer import CreateBookingByTrainerRequest, CreateBookingByTrainerUseCase

from src.application.use_cases.booking.mark_attendance import MarkBookingAttendanceRequest, MarkBookingAttendanceUseCase

from src.application.use_cases.digest.send_trainer_digests import SendTrainerDigestsRequest, SendTrainerDigestsUseCase

from src.application.use_cases.trainer_reminder_settings.update_digest import UpdateTrainerDigestSettingsRequest, UpdateTrainerDigestSettingsUseCase

from src.application.use_cases.package.create import CreateClientPackageRequest, CreateClientPackageUseCase

from src.application.use_cases.package.manage import ManageClientPackageRequest, ManageClientPackageUseCase

from src.application.use_cases.package.get_by_client import GetClientPackagesRequest, GetClientPackagesUseCase

from src.application.use_cases.package.get_balances import GetClientBalancesRequest, GetClientBalancesUseCase

from src.application.use_cases.booking.mark_paid import MarkBookingsPaidRequest, MarkBookingsPaidUseCase

from src.application.use_cases.booking.attendance import SendAttendanceRequestsRequest, SendAttendanceRequestsUseCase

from src.application.use_cases.booking.attendance import ConfirmAttendanceRequest, ConfirmAttendanceUseCase

from src.application.use_cases.client.get_inactive import GetInactiveClientsRequest, GetInactiveClientsUseCase

from src.application.use_cases.client.invite_back import InviteClientBackRequest, InviteClientBackUseCase

from src.application.use_cases.vacation.preview import PreviewVacationRequest, PreviewVacationUseCase

from src.application.use_cases.vacation.create import CreateVacationRequest, CreateVacationUseCase

from src.application.use_cases.vacation.manage import GetVacationsRequest, GetVacationsUseCase

from src.application.use_cases.vacation.manage import DeleteVacationRequest, DeleteVacationUseCase


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
        get_clients_by_trainer_use_case: GetClientsByTrainerUseCase,
        get_active_invite_link_use_case: GetActiveInviteLinkUseCase,
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
        mark_past_bookings_completed_use_case: MarkPastBookingsCompletedUseCase,
        get_trainer_stats_use_case: GetTrainerStatsUseCase,
        get_client_answers_use_case: GetClientAnswersUseCase,
        update_trainer_reminder_settings_use_case: UpdateTrainerReminderSettingsUseCase,
        get_trainer_reminder_settings_use_case: GetTrainerReminderSettingsUseCase,
        mark_booking_completed_use_case: MarkBookingCompletedUseCase,
        get_active_recurring_bookings_by_client_use_case: GetActiveRecurringBookingsByClientUseCase,
        create_program_request_use_case: CreateProgramRequestUseCase,
        create_consultation_request_use_case: CreateConsultationRequestUseCase,
        create_feedback_use_case: CreateFeedbackUseCase,
        get_client_requests_by_trainer_use_case: GetClientRequestsByTrainerUseCase,
        get_client_request_by_id_use_case: GetClientRequestByIdUseCase,
        update_client_request_status_use_case: UpdateClientRequestStatusUseCase,
        get_active_faq_items_use_case: GetActiveFaqItemsUseCase,
        get_faq_item_by_id_use_case: GetFaqItemByIdUseCase,
        add_faq_item_use_case: AddFaqItemUseCase,
        deactivate_faq_item_use_case: DeactivateFaqItemUseCase,
        set_slot_blocked_use_case: SetSlotBlockedUseCase,
        set_day_blocked_use_case: SetDayBlockedUseCase,
        get_upcoming_bookings_by_client_use_case: GetUpcomingBookingsByClientUseCase,
        update_client_answers_use_case: UpdateClientAnswersUseCase,
        send_plan_next_training_reminder_use_case: SendPlanNextTrainingReminderUseCase,
        grant_subscription_use_case: GrantSubscriptionUseCase,
        check_expiring_subscriptions_use_case: CheckExpiringSubscriptionsUseCase,
        get_subscriptions_by_trainer_use_case: GetSubscriptionsByTrainerUseCase,
        get_user_access_use_case: GetUserAccessUseCase,
        set_trainer_blocked_use_case: SetTrainerBlockedUseCase,
        set_client_blocked_use_case: SetClientBlockedUseCase,
        search_clients_use_case: SearchClientsUseCase,
        get_all_trainers_use_case: GetAllTrainersUseCase,
        get_admin_overview_stats_use_case: GetAdminOverviewStatsUseCase,
        get_admin_trainer_report_use_case: GetAdminTrainerReportUseCase,
        export_report_use_case: ExportReportUseCase,
        enqueue_mailing_use_case: EnqueueMailingUseCase,
        execute_mailing_use_case: ExecuteMailingUseCase,
        execute_mailing_batch_use_case: ExecuteMailingBatchUseCase,
        is_trainer_available_use_case: IsTrainerAvailableUseCase,
        create_subscription_payment_use_case: CreateSubscriptionPaymentUseCase,
        confirm_payment_use_case: ConfirmPaymentUseCase,
        reject_payment_use_case: RejectPaymentUseCase,
        get_payment_methods_use_case: GetPaymentMethodsUseCase,
        get_payment_by_external_id_use_case: GetPaymentByExternalIdUseCase,
        get_admin_analytics_use_case: GetAdminAnalyticsUseCase,
        track_user_activity_use_case: TrackUserActivityUseCase,
        set_bot_blocked_by_user_use_case: SetBotBlockedByUserUseCase,
        create_offline_client_use_case: CreateOfflineClientUseCase,
        update_client_field_use_case: UpdateClientFieldUseCase,
        delete_offline_client_use_case: DeleteOfflineClientUseCase,
        claim_client_invite_use_case: ClaimClientInviteUseCase,
        get_client_by_invite_token_use_case: GetClientByInviteTokenUseCase,
        get_booking_views_use_case: GetBookingViewsUseCase,
        create_booking_by_trainer_use_case: CreateBookingByTrainerUseCase,
        mark_booking_attendance_use_case: MarkBookingAttendanceUseCase,
        send_trainer_digests_use_case: SendTrainerDigestsUseCase,
        update_trainer_digest_settings_use_case: UpdateTrainerDigestSettingsUseCase,
        create_client_package_use_case: CreateClientPackageUseCase,
        manage_client_package_use_case: ManageClientPackageUseCase,
        get_client_packages_use_case: GetClientPackagesUseCase,
        get_client_balances_use_case: GetClientBalancesUseCase,
        mark_bookings_paid_use_case: MarkBookingsPaidUseCase,
        send_attendance_requests_use_case: SendAttendanceRequestsUseCase,
        confirm_attendance_use_case: ConfirmAttendanceUseCase,
        get_inactive_clients_use_case: GetInactiveClientsUseCase,
        invite_client_back_use_case: InviteClientBackUseCase,
        preview_vacation_use_case: PreviewVacationUseCase,
        create_vacation_use_case: CreateVacationUseCase,
        get_vacations_use_case: GetVacationsUseCase,
        delete_vacation_use_case: DeleteVacationUseCase,
    ) -> Mediator:
        mediator = Mediator()

        mediator.register(
            MaintainCalendarBufferRequest, maintain_calendar_buffer_use_case
        )
        mediator.register(GetDaySlotsRequest, get_day_slots_use_case)
        mediator.register(GetAvailableSlotsRequest, get_available_slots_use_case)
        mediator.register(GetWeekGridRequest, get_week_grid_use_case)
        mediator.register(GetTimeColumnsRequest, get_time_column_use_case)
        mediator.register(
            GetDayAvailabilityMapRequest, get_day_availability_map_use_case
        )
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
        mediator.register(
            GetActiveSlotTemplatesRequest, get_active_slot_template_use_case
        )
        mediator.register(
            DeactivateSlotTemplateRequest, deactivate_slot_template_use_case
        )
        mediator.register(GetClientsByTrainerRequest, get_clients_by_trainer_use_case)
        mediator.register(GetActiveInviteLinkRequest, get_active_invite_link_use_case)
        mediator.register(GetActivePricePlansRequest, get_active_price_plans_use_case)
        mediator.register(
            GetActiveSubscriptionRequest, get_active_subscription_use_case
        )
        mediator.register(RegisterTrainerRequest, register_trainer_use_case)
        mediator.register(
            CreateTrainerInviteLinkRequest, create_trainer_invite_link_use_case
        )
        mediator.register(
            SyncWeekdaySlotTemplatesRequest, sync_weekday_slot_tamplate_use_case
        )
        mediator.register(
            GetTrainerBookingSettingsRequest, get_trainer_booking_settings_use_case
        )
        mediator.register(
            UpdateTrainerBookingSettingsRequest,
            update_trainer_booking_settings_use_case,
        )
        mediator.register(
            CountActiveBookingsBySlotIdsRequest,
            count_active_booking_by_slot_ids_use_case,
        )
        mediator.register(
            GetTrainerPricingRuleRequest, get_trainer_pricing_rule_use_case
        )
        mediator.register(
            UpdateTrainerPricingRuleRequest, update_trainer_pricing_rule_use_case
        )
        mediator.register(UpdateTrainerProfileRequest, update_trainer_profile_use_case)
        mediator.register(
            GetClientsByTrainerIdRequest, get_clients_by_trainer_id_use_case
        )
        mediator.register(SendTrainingReminderRequest, send_training_reminder_use_case)
        mediator.register(
            GetActiveRegistrationQuestionsRequest,
            get_active_registration_questions_use_case,
        )
        mediator.register(
            GetAllRegistrationQuestionsRequest, get_all_registration_question_use_case
        )
        mediator.register(AddCustomQuestionRequest, add_custom_question_use_case)
        mediator.register(DeleteCustomQuestionRequest, delete_custom_question_use_case)
        mediator.register(
            UpdateQuestionOptionsRequest, update_question_options_use_case
        )
        mediator.register(
            GetRegistrationQuestionByIdRequest, get_registration_question_by_id_use_case
        )
        mediator.register(GetClientByIdRequest, get_client_by_id_use_case)
        mediator.register(
            GetDayAvailabilityMapForAssignmentRequest,
            get_day_availability_map_for_assignment_use_case,
        )
        mediator.register(AddRecurringBookingRequest, add_recurring_booking_use_case)
        mediator.register(
            MaintainRecurringBookingsRequest, maintain_recurring_booking_use_case
        )
        mediator.register(RescheduleBookingRequest, reschedule_booking_use_case)
        mediator.register(GetBookingByIdRequest, get_booking_by_id_use_case)
        mediator.register(
            ChangeRecurringBookingScheduleRequest,
            change_recurring_booking_schedule_use_case,
        )
        mediator.register(
            DeactivateRecurringBookingRequest, deactivate_reccuring_booking_use_case
        )
        mediator.register(
            GetActiveRecurringBookingsByTrainerRequest,
            get_active_recurring_bookings_by_trainer_use_case,
        )
        mediator.register(
            GetRecurringBookingByIdRequest, get_recurring_booking_by_id_use_case
        )
        mediator.register(
            MarkPastBookingsCompletedRequest, mark_past_bookings_completed_use_case
        )
        mediator.register(GetTrainerStatsRequest, get_trainer_stats_use_case)
        mediator.register(
            GetClientAnswersRequest, get_client_answers_use_case
        )
        mediator.register(UpdateTrainerReminderSettingsRequest, update_trainer_reminder_settings_use_case)
        mediator.register(GetTrainerReminderSettingsRequest, get_trainer_reminder_settings_use_case)
        mediator.register(MarkBookingCompletedRequest, mark_booking_completed_use_case)
        mediator.register(GetActiveRecurringBookingsByClientRequest, get_active_recurring_bookings_by_client_use_case)
        mediator.register(CreateProgramRequestRequest, create_program_request_use_case)
        mediator.register(CreateConsultationRequestRequest, create_consultation_request_use_case)
        mediator.register(CreateFeedbackRequest, create_feedback_use_case)
        mediator.register(GetClientRequestsByTrainerRequest, get_client_requests_by_trainer_use_case)
        mediator.register(GetClientRequestByIdRequest, get_client_request_by_id_use_case)
        mediator.register(UpdateClientRequestStatusRequest, update_client_request_status_use_case)
        mediator.register(GetActiveFaqItemsRequest, get_active_faq_items_use_case)
        mediator.register(GetFaqItemByIdRequest, get_faq_item_by_id_use_case)
        mediator.register(AddFaqItemRequest, add_faq_item_use_case)
        mediator.register(DeactivateFaqItemRequest, deactivate_faq_item_use_case)
        mediator.register(SetSlotBlockedRequest, set_slot_blocked_use_case)
        mediator.register(SetDayBlockedRequest, set_day_blocked_use_case)
        mediator.register(GetUpcomingBookingsByClientRequest, get_upcoming_bookings_by_client_use_case)
        mediator.register(UpdateClientAnswersRequest, update_client_answers_use_case)
        mediator.register(SendPlanNextTrainingReminderRequest, send_plan_next_training_reminder_use_case)

        mediator.register(GrantSubscriptionRequest, grant_subscription_use_case)
        mediator.register(CheckExpiringSubscriptionsRequest, check_expiring_subscriptions_use_case)
        mediator.register(GetSubscriptionsByTrainerRequest, get_subscriptions_by_trainer_use_case)
        mediator.register(GetUserAccessRequest, get_user_access_use_case)
        mediator.register(SetTrainerBlockedRequest, set_trainer_blocked_use_case)
        mediator.register(SetClientBlockedRequest, set_client_blocked_use_case)
        mediator.register(SearchClientsRequest, search_clients_use_case)
        mediator.register(GetAllTrainersRequest, get_all_trainers_use_case)
        mediator.register(GetAdminOverviewStatsRequest, get_admin_overview_stats_use_case)
        mediator.register(GetAdminTrainerReportRequest, get_admin_trainer_report_use_case)
        mediator.register(ExportReportRequest, export_report_use_case)
        mediator.register(EnqueueMailingRequest, enqueue_mailing_use_case)
        mediator.register(ExecuteMailingRequest, execute_mailing_use_case)
        mediator.register(ExecuteMailingBatchRequest, execute_mailing_batch_use_case)
        mediator.register(IsTrainerAvailableRequest, is_trainer_available_use_case)

        mediator.register(CreateSubscriptionPaymentRequest, create_subscription_payment_use_case)
        mediator.register(ConfirmPaymentRequest, confirm_payment_use_case)
        mediator.register(RejectPaymentRequest, reject_payment_use_case)
        mediator.register(GetPaymentMethodsRequest, get_payment_methods_use_case)
        mediator.register(GetPaymentByExternalIdRequest, get_payment_by_external_id_use_case)

        mediator.register(GetAdminAnalyticsRequest, get_admin_analytics_use_case)
        mediator.register(TrackUserActivityRequest, track_user_activity_use_case)
        mediator.register(SetBotBlockedByUserRequest, set_bot_blocked_by_user_use_case)

        mediator.register(CreateOfflineClientRequest, create_offline_client_use_case)
        mediator.register(UpdateClientFieldRequest, update_client_field_use_case)
        mediator.register(DeleteOfflineClientRequest, delete_offline_client_use_case)
        mediator.register(ClaimClientInviteRequest, claim_client_invite_use_case)
        mediator.register(GetClientByInviteTokenRequest, get_client_by_invite_token_use_case)
        mediator.register(GetBookingViewsRequest, get_booking_views_use_case)
        mediator.register(CreateBookingByTrainerRequest, create_booking_by_trainer_use_case)
        mediator.register(MarkBookingAttendanceRequest, mark_booking_attendance_use_case)
        mediator.register(SendTrainerDigestsRequest, send_trainer_digests_use_case)
        mediator.register(UpdateTrainerDigestSettingsRequest, update_trainer_digest_settings_use_case)
        mediator.register(CreateClientPackageRequest, create_client_package_use_case)
        mediator.register(ManageClientPackageRequest, manage_client_package_use_case)
        mediator.register(GetClientPackagesRequest, get_client_packages_use_case)
        mediator.register(GetClientBalancesRequest, get_client_balances_use_case)
        mediator.register(MarkBookingsPaidRequest, mark_bookings_paid_use_case)
        mediator.register(SendAttendanceRequestsRequest, send_attendance_requests_use_case)
        mediator.register(ConfirmAttendanceRequest, confirm_attendance_use_case)
        mediator.register(GetInactiveClientsRequest, get_inactive_clients_use_case)
        mediator.register(InviteClientBackRequest, invite_client_back_use_case)
        mediator.register(PreviewVacationRequest, preview_vacation_use_case)
        mediator.register(CreateVacationRequest, create_vacation_use_case)
        mediator.register(GetVacationsRequest, get_vacations_use_case)
        mediator.register(DeleteVacationRequest, delete_vacation_use_case)
        return mediator
