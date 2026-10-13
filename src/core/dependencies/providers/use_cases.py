from dishka import Provider, provide, Scope

from src.application.interfaces.booking_scheduler import BookingScheduler
from src.application.use_cases.booking.cancel import CancelBookingUseCase
from src.application.use_cases.booking.confirm import ConfirmBookingUseCase
from src.application.use_cases.booking.count_active_by_slot_ids import (
    CountActiveBookingsBySlotIdsUseCase,
)
from src.application.use_cases.booking.get_by_id import GetBookingByIdUseCase
from src.application.use_cases.booking.get_history_by_trainer import GetBookingsHistoryByTrainerUseCase
from src.application.use_cases.booking.mark_completed import MarkBookingCompletedUseCase
from src.application.use_cases.booking.reschedule import RescheduleBookingUseCase
from src.application.use_cases.booking.send_reminder import SendTrainingReminderUseCase
from src.application.use_cases.calendar.get_day_availability_map_assignment import GetDayAvailabilityMapForAssignmentUseCase
from src.application.use_cases.client.get_answers_by_id import GetClientAnswersUseCase
from src.application.use_cases.client.get_by_id import GetClientByIdUseCase
from src.application.use_cases.recurring_booking.add import AddRecurringBookingUseCase
from src.application.use_cases.recurring_booking.deactivate import DeactivateRecurringBookingUseCase
from src.application.use_cases.recurring_booking.get_active_by_client import GetActiveRecurringBookingsByClientUseCase
from src.application.use_cases.recurring_booking.get_by_id import GetRecurringBookingByIdUseCase
from src.application.use_cases.recurring_booking.maintain import MaintainRecurringBookingsUseCase
from src.application.use_cases.registration_questions.add_custom import AddCustomQuestionUseCase
from src.application.use_cases.registration_questions.delete import DeleteCustomQuestionUseCase
from src.application.use_cases.registration_questions.get_active import (
    GetActiveRegistrationQuestionsUseCase,
)
from src.application.use_cases.client.get_clients_by_trainer import (
    GetClientsByTrainerIdUseCase,
)
from src.application.use_cases.invite_link.create import CreateTrainerInviteLinkUseCase
from src.application.use_cases.invite_link.get_active import GetActiveInviteLinkUseCase
from src.application.use_cases.registration_questions.get_all import GetAllRegistrationQuestionsUseCase
from src.application.use_cases.registration_questions.update import UpdateQuestionOptionsUseCase
from src.application.use_cases.registration_questions.get_by_id import (
    GetRegistrationQuestionByIdUseCase,
)
from src.application.use_cases.slot_template.create import CreateSlotTemplateUseCase
from src.application.use_cases.slot_template.deactivate import (
    DeactivateSlotTemplateUseCase,
)
from src.application.use_cases.slot_template.get_active import (
    GetActiveSlotTemplatesUseCase,
)
from src.application.use_cases.slot_template.sync_weekday import (
    SyncWeekdaySlotTemplatesUseCase,
)
from src.application.use_cases.stats.get_trainer import GetTrainerStatsUseCase
from src.application.use_cases.subscription.get_active import (
    GetActiveSubscriptionUseCase,
)
from src.application.use_cases.subscription.get_active_price_plans import (
    GetActivePricePlansUseCase,
)
from src.application.use_cases.trainer.get_by_tg_id import GetTrainerByTgIdUseCase
from src.application.use_cases.trainer.get_clients_by_trainer import (
    GetClientsByTrainerUseCase,
)
from src.application.use_cases.trainer.get_upcoming_bookings_by_trainer import (
    GetUpcomingBookingsByTrainerUseCase,
)
from src.application.use_cases.trainer.register import RegisterTrainerUseCase
from src.application.use_cases.trainer.update import UpdateTrainerProfileUseCase
from src.application.use_cases.trainer_booking_settings.get_by_id import (
    GetTrainerBookingSettingsUseCase,
)
from src.application.use_cases.trainer_booking_settings.update import (
    UpdateTrainerBookingSettingsUseCase,
)
from src.application.use_cases.trainer_pricing_rule.get_by_id import (
    GetTrainerPricingRuleUseCase,
)
from src.application.use_cases.trainer_pricing_rule.update import (
    UpdateTrainerPricingRuleUseCase,
)
from src.application.use_cases.trainer_reminder_settings.get_by_trainer_id import GetTrainerReminderSettingsUseCase
from src.application.use_cases.trainer_reminder_settings.update import UpdateTrainerReminderSettingsUseCase
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.client import ClientRepository
from src.domain.repositories.client_answer import ClientAnswerRepository
from src.domain.repositories.invite_link import TrainerInviteLinkRepository
from src.domain.repositories.recurring_booking import RecurringBookingRepository
from src.domain.repositories.registration_question import RegistrationQuestionRepository
from src.domain.repositories.slot_template import SlotTemplateRepository
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.subscription_price_plan import (
    SubscriptionPricePlanRepository,
)
from src.domain.repositories.trainer import TrainerRepository
from src.domain.repositories.trainer_booking_settings import (
    TrainerBookingSettingsRepository,
)
from src.domain.repositories.trainer_pricing_rule import TrainerPricingRuleRepository
from src.domain.repositories.trainer_reminder_settings import TrainerReminderSettingsRepository
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
from src.application.use_cases.recurring_booking.change import (
    ChangeRecurringBookingScheduleUseCase,
)
from src.application.use_cases.recurring_booking.get_all_active_by_trainer import (
    GetActiveRecurringBookingsByTrainerUseCase,
)
from src.application.use_cases.booking.mark_past_completed import (
    MarkPastBookingsCompletedUseCase,
)
from src.application.use_cases.calendar.get_slot_by_id import GetSlotByIdUseCase
from src.application.use_cases.client.register import RegisterClientUseCase
from src.application.use_cases.client.get_by_tg_id import GetClientByTgIdUseCase
from src.application.use_cases.invite_link.resolve import ResolveInviteLinkUseCase
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdUseCase
from src.application.interfaces.notification_service import NotificationService

from src.infrastructure.database.transaction_manager.base import TransactionManager

from src.application.use_cases.client_request.create_program import CreateProgramRequestUseCase
from src.application.use_cases.client_request.create_consultation import CreateConsultationRequestUseCase
from src.application.use_cases.client_request.create_feedback import CreateFeedbackUseCase
from src.application.use_cases.client_request.get_by_trainer import GetClientRequestsByTrainerUseCase
from src.application.use_cases.client_request.get_by_id import GetClientRequestByIdUseCase
from src.application.use_cases.client_request.update_status import UpdateClientRequestStatusUseCase
from src.application.use_cases.faq.get_active import GetActiveFaqItemsUseCase
from src.application.use_cases.faq.get_by_id import GetFaqItemByIdUseCase
from src.application.use_cases.faq.add import AddFaqItemUseCase
from src.application.use_cases.faq.deactivate import DeactivateFaqItemUseCase
from src.application.use_cases.calendar.set_slot_blocked import SetSlotBlockedUseCase
from src.application.use_cases.calendar.set_day_blocked import SetDayBlockedUseCase
from src.application.use_cases.booking.get_upcoming_by_client import GetUpcomingBookingsByClientUseCase
from src.application.use_cases.client.update_answers import UpdateClientAnswersUseCase
from src.application.use_cases.booking.send_plan_next_reminder import SendPlanNextTrainingReminderUseCase
from src.domain.repositories.consultation import ConsultationRequestRepository
from src.domain.repositories.faq import FaqRepository
from src.domain.repositories.feedback import FeedbackRepository
from src.domain.repositories.program import ProgramRequestRepository

from src.application.use_cases.subscription.grant import GrantSubscriptionUseCase
from src.application.use_cases.subscription.check_expiring import CheckExpiringSubscriptionsUseCase
from src.application.use_cases.subscription.get_by_trainer import GetSubscriptionsByTrainerUseCase
from src.application.use_cases.access.get_user_access import GetUserAccessUseCase
from src.application.use_cases.trainer.set_blocked import SetTrainerBlockedUseCase
from src.application.use_cases.client.set_blocked import SetClientBlockedUseCase
from src.application.use_cases.client.search import SearchClientsUseCase
from src.application.use_cases.trainer.get_all import GetAllTrainersUseCase
from src.application.use_cases.admin.get_overview_stats import GetAdminOverviewStatsUseCase
from src.application.use_cases.admin.get_trainer_report import GetAdminTrainerReportUseCase
from src.application.use_cases.admin.export_report import ExportReportUseCase
from src.application.use_cases.mailing.enqueue import EnqueueMailingUseCase
from src.application.use_cases.mailing.execute import ExecuteMailingUseCase
from src.application.use_cases.mailing.execute_batch import ExecuteMailingBatchUseCase
from src.application.interfaces.mailing_progress import MailingProgressStore
from src.application.interfaces.task_queue import TaskQueue

from src.application.use_cases.access.is_trainer_available import IsTrainerAvailableUseCase

from src.application.use_cases.payment.create_subscription_payment import CreateSubscriptionPaymentUseCase
from src.application.use_cases.payment.confirm import ConfirmPaymentUseCase
from src.application.use_cases.payment.reject import RejectPaymentUseCase
from src.application.use_cases.payment.get_methods import GetPaymentMethodsUseCase
from src.application.use_cases.payment.get_by_external_id import GetPaymentByExternalIdUseCase
from src.application.services.payment_provider_registry import PaymentProviderRegistry
from src.domain.repositories.payment import PaymentRepository
from src.domain.repositories.bot_user import BotUserRepository
from src.domain.constants import TRAINER_TRIAL_DAYS
from src.application.use_cases.admin.get_analytics import GetAdminAnalyticsUseCase
from src.application.use_cases.bot_user.track_activity import TrackUserActivityUseCase
from src.application.use_cases.bot_user.set_bot_blocked import SetBotBlockedByUserUseCase


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
        self,
        calendar_service: CalendarService,
        booking_repo: BookingRepository,
    ) -> GetDayAvailabilityMapUseCase:
        return GetDayAvailabilityMapUseCase(
            calendar_service=calendar_service,
            booking_repo=booking_repo,
        )

    @provide
    def get_slot_by_id_use_case(
        self, slot_repo: CalendarSlotRepository
    ) -> GetSlotByIdUseCase:
        return GetSlotByIdUseCase(slot_repo=slot_repo)

    @provide
    def register_client_use_case(
        self,
        client_repo: ClientRepository,
        answer_repo: ClientAnswerRepository,
        transaction_manager: TransactionManager,
    ) -> RegisterClientUseCase:
        return RegisterClientUseCase(
            client_repo=client_repo,
            answer_repo=answer_repo,
            transaction_manager=transaction_manager,
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
        pricing_rule_repo: TrainerPricingRuleRepository,
        booking_settings_repo: TrainerBookingSettingsRepository,
        answer_repo: ClientAnswerRepository,
        question_repo: RegistrationQuestionRepository,
        notification_service: NotificationService,
        transaction_manager: TransactionManager,
    ) -> CreateBookingUseCase:
        return CreateBookingUseCase(
            calendar_service=calendar_service,
            booking_repo=booking_repo,
            trainer_repo=trainer_repo,
            client_repo=client_repo,
            pricing_rule_repo=pricing_rule_repo,
            booking_settings_repo=booking_settings_repo,
            answer_repo=answer_repo,
            question_repo=question_repo,
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
        trainer_repo: TrainerRepository,
        slot_repo: CalendarSlotRepository,
        reminder_settings_repo: TrainerReminderSettingsRepository,
        booking_scheduler: BookingScheduler,
        notification_service: NotificationService,
        transaction_manager: TransactionManager,
    ) -> ConfirmBookingUseCase:
        return ConfirmBookingUseCase(
            booking_repo=booking_repo,
            client_repo=client_repo,
            trainer_repo=trainer_repo,
            slot_repo=slot_repo,
            reminder_settings_repo=reminder_settings_repo,
            booking_scheduler=booking_scheduler,
            notification_service=notification_service,
            transaction_manager=transaction_manager,
        )

    @provide
    def cancel_booking_use_case(
        self,
        booking_repo: BookingRepository,
        client_repo: ClientRepository,
        trainer_repo: TrainerRepository,
        slot_repo: CalendarSlotRepository,
        calendar_service: CalendarService,
        booking_scheduler: BookingScheduler,
        notification_service: NotificationService,
        transaction_manager: TransactionManager,
    ) -> CancelBookingUseCase:
        return CancelBookingUseCase(
            booking_repo=booking_repo,
            client_repo=client_repo,
            trainer_repo=trainer_repo,
            slot_repo=slot_repo,
            calendar_service=calendar_service,
            booking_scheduler=booking_scheduler,
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
        booking_settings_repo: TrainerBookingSettingsRepository,
        question_repo: RegistrationQuestionRepository,
        subscription_repo: TrainerSubscriptionRepository,
        transaction_manager: TransactionManager,
    ) -> RegisterTrainerUseCase:
        return RegisterTrainerUseCase(
            trainer_repo=trainer_repo,
            invite_link_repo=invite_link_repo,
            booking_settings_repo=booking_settings_repo,
            question_repo=question_repo,
            subscription_repo=subscription_repo,
            trial_days=TRAINER_TRIAL_DAYS,
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

    @provide
    def get_trainer_booking_settings_use_case(
        self,
        settings_repo: TrainerBookingSettingsRepository,
    ) -> GetTrainerBookingSettingsUseCase:
        return GetTrainerBookingSettingsUseCase(
            settings_repo=settings_repo,
        )

    @provide
    def update_trainer_booking_settings_use_case(
        self,
        settings_repo: TrainerBookingSettingsRepository,
        transaction_manager: TransactionManager,
    ) -> UpdateTrainerBookingSettingsUseCase:
        return UpdateTrainerBookingSettingsUseCase(
            settings_repo=settings_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def count_active_booking_by_slot_ids_use_case(
        self,
        booking_repo: BookingRepository,
    ) -> CountActiveBookingsBySlotIdsUseCase:
        return CountActiveBookingsBySlotIdsUseCase(
            booking_repo=booking_repo,
        )

    @provide
    def get_trainer_pricing_rule_use_case(
        self,
        pricing_repo: TrainerPricingRuleRepository,
    ) -> GetTrainerPricingRuleUseCase:
        return GetTrainerPricingRuleUseCase(
            pricing_repo=pricing_repo,
        )

    @provide
    def update_trainer_pricing_rule_use_case(
        self,
        pricing_repo: TrainerPricingRuleRepository,
        transaction_manager: TransactionManager,
    ) -> UpdateTrainerPricingRuleUseCase:
        return UpdateTrainerPricingRuleUseCase(
            pricing_repo=pricing_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def update_trainer_profile_use_case(
        self,
        trainer_repo: TrainerRepository,
        transaction_manager: TransactionManager,
    ) -> UpdateTrainerProfileUseCase:
        return UpdateTrainerProfileUseCase(
            trainer_repo=trainer_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_clients_by_trainer_id_use_case(
        self,
        client_repo: ClientRepository,
    ) -> GetClientsByTrainerIdUseCase:
        return GetClientsByTrainerIdUseCase(
            client_repo=client_repo,
        )

    @provide
    def send_training_reminder_use_case(
        self,
        booking_repo: BookingRepository,
        client_repo: ClientRepository,
        trainer_repo: TrainerRepository,
        slot_repo: CalendarSlotRepository,
        notification_service: NotificationService,
    ) -> SendTrainingReminderUseCase:
        return SendTrainingReminderUseCase(
            booking_repo=booking_repo,
            client_repo=client_repo,
            trainer_repo=trainer_repo,
            slot_repo=slot_repo,
            notification_service=notification_service,
        )

    @provide
    def get_active_registration_questions_use_case(
        self,
        question_repo: RegistrationQuestionRepository,
    ) -> GetActiveRegistrationQuestionsUseCase:
        return GetActiveRegistrationQuestionsUseCase(
            question_repo=question_repo,
        )

    @provide
    def get_all_registration_question_use_case(
        self,
        question_repo: RegistrationQuestionRepository,
    ) -> GetAllRegistrationQuestionsUseCase:
        return GetAllRegistrationQuestionsUseCase(
            question_repo=question_repo,
        )

    @provide
    def add_custom_question_use_case(
        self,
        question_repo: RegistrationQuestionRepository,
        transaction_manager: TransactionManager,
    ) -> AddCustomQuestionUseCase:
        return AddCustomQuestionUseCase(
            question_repo=question_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def delete_custom_question_use_case(
        self,
        question_repo: RegistrationQuestionRepository,
        transaction_manager: TransactionManager,
    ) -> DeleteCustomQuestionUseCase:
        return DeleteCustomQuestionUseCase(
            question_repo=question_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def update_question_options_use_case(
        self,
        question_repo: RegistrationQuestionRepository,
        transaction_manager: TransactionManager,
    ) -> UpdateQuestionOptionsUseCase:
        return UpdateQuestionOptionsUseCase(
            question_repo=question_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_registration_question_by_id_use_case(
        self,
        question_repo: RegistrationQuestionRepository,
    ) -> GetRegistrationQuestionByIdUseCase:
        return GetRegistrationQuestionByIdUseCase(
            question_repo=question_repo,
        )

    @provide
    def get_client_by_id_use_case(
        self,
        client_repo: ClientRepository,
    ) -> GetClientByIdUseCase:
        return GetClientByIdUseCase(
            client_repo=client_repo,
        )

    @provide
    def get_day_availability_map_for_assignment_use_case(
        self,
        calendar_service: CalendarService,
    ) -> GetDayAvailabilityMapForAssignmentUseCase:
        return GetDayAvailabilityMapForAssignmentUseCase(
            calendar_service=calendar_service,
        )

    @provide
    def add_recurring_booking_use_case(
        self,
        recurring_repo: RecurringBookingRepository,
        slot_repo: CalendarSlotRepository,
        booking_repo: BookingRepository,
        calendar_service: CalendarService,
        pricing_rule_repo: TrainerPricingRuleRepository,
        client_repo: ClientRepository,
        trainer_repo: TrainerRepository,
        reminder_settings_repo: TrainerReminderSettingsRepository,
        notification_service: NotificationService,
        booking_scheduler: BookingScheduler,
        transaction_manager: TransactionManager,
    ) -> AddRecurringBookingUseCase:
        return AddRecurringBookingUseCase(
            recurring_repo=recurring_repo,
            slot_repo=slot_repo,
            booking_repo=booking_repo,
            calendar_service=calendar_service,
            pricing_rule_repo=pricing_rule_repo,
            client_repo=client_repo,
            trainer_repo=trainer_repo,
            reminder_settings_repo=reminder_settings_repo,
            notification_service=notification_service,
            booking_scheduler=booking_scheduler,
            transaction_manager=transaction_manager,
        )

    @provide
    def maintain_recurring_booking_use_case(
        self,
        recurring_repo: RecurringBookingRepository,
        booking_repo: BookingRepository,
        slot_repo: CalendarSlotRepository,
        calendar_service: CalendarService,
        trainer_repo: TrainerRepository,
        client_repo: ClientRepository,
        reminder_settings_repo: TrainerReminderSettingsRepository,
        pricing_rule_repo: TrainerPricingRuleRepository,
        notification_service: NotificationService,
        booking_scheduler: BookingScheduler,
        transaction_manager: TransactionManager,
    ) -> MaintainRecurringBookingsUseCase:
        return MaintainRecurringBookingsUseCase(
            recurring_repo=recurring_repo,
            booking_repo=booking_repo,
            slot_repo=slot_repo,
            calendar_service=calendar_service,
            trainer_repo=trainer_repo,
            client_repo=client_repo,
            reminder_settings_repo=reminder_settings_repo,
            pricing_rule_repo=pricing_rule_repo,
            notification_service=notification_service,
            booking_scheduler=booking_scheduler,
            transaction_manager=transaction_manager,
        )

    @provide
    def reschedule_booking_use_case(
        self,
        booking_repo: BookingRepository,
        client_repo: ClientRepository,
        slot_repo: CalendarSlotRepository,
        calendar_service: CalendarService,
        pricing_rule_repo: TrainerPricingRuleRepository,
        reminder_settings_repo: TrainerReminderSettingsRepository,
        notification_service: NotificationService,
        booking_scheduler: BookingScheduler,
        transaction_manager: TransactionManager,
    ) -> RescheduleBookingUseCase:
        return RescheduleBookingUseCase(
            booking_repo=booking_repo,
            client_repo=client_repo,
            slot_repo=slot_repo,
            calendar_service=calendar_service,
            pricing_rule_repo=pricing_rule_repo,
            reminder_settings_repo=reminder_settings_repo,
            notification_service=notification_service,
            booking_scheduler=booking_scheduler,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_booking_by_id_use_case(
        self,
        booking_repo: BookingRepository,
    ) -> GetBookingByIdUseCase:
        return GetBookingByIdUseCase(
            booking_repo=booking_repo,
        )

    @provide
    def change_recurring_booking_schedule_use_case(
        self,
        recurring_repo: RecurringBookingRepository,
        booking_repo: BookingRepository,
        reschedule_use_case: RescheduleBookingUseCase,
        transaction_manager: TransactionManager,
    ) -> ChangeRecurringBookingScheduleUseCase:
        return ChangeRecurringBookingScheduleUseCase(
            recurring_repo=recurring_repo,
            booking_repo=booking_repo,
            reschedule_use_case=reschedule_use_case,
            transaction_manager=transaction_manager,
        )

    @provide
    def deactivate_reccuring_booking_use_case(
        self,
        recurring_repo: RecurringBookingRepository,
        booking_repo: BookingRepository,
        client_repo: ClientRepository,
        cancel_use_case: CancelBookingUseCase,
        notification_service: NotificationService,
        transaction_manager: TransactionManager,
    ) -> DeactivateRecurringBookingUseCase:
        return DeactivateRecurringBookingUseCase(
            recurring_repo=recurring_repo,
            booking_repo=booking_repo,
            client_repo=client_repo,
            cancel_use_case=cancel_use_case,
            notification_service=notification_service,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_active_recurring_bookings_by_trainer_use_case(
        self,
        recurring_repo: RecurringBookingRepository,
    ) -> GetActiveRecurringBookingsByTrainerUseCase:
        return GetActiveRecurringBookingsByTrainerUseCase(
            recurring_repo=recurring_repo,
        )

    @provide
    def get_recurring_booking_by_id_use_case(
        self,
        recurring_repo: RecurringBookingRepository,
    ) -> GetRecurringBookingByIdUseCase:
        return GetRecurringBookingByIdUseCase(
            recurring_repo=recurring_repo,
        )

    @provide
    def mark_past_bookings_completed_use_case(
        self,
        booking_repo: BookingRepository,
        transaction_manager: TransactionManager,
    ) -> MarkPastBookingsCompletedUseCase:
        return MarkPastBookingsCompletedUseCase(
            booking_repo=booking_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_trainer_stats_use_case(
        self,
        client_repo: ClientRepository,
        booking_repo: BookingRepository,
        recurring_repo: RecurringBookingRepository,
        program_repo: ProgramRequestRepository,
        consultation_repo: ConsultationRequestRepository,
        feedback_repo: FeedbackRepository,
    ) -> GetTrainerStatsUseCase:
        return GetTrainerStatsUseCase(
            client_repo=client_repo,
            booking_repo=booking_repo,
            recurring_repo=recurring_repo,
            program_repo=program_repo,
            consultation_repo=consultation_repo,
            feedback_repo=feedback_repo,
        )

    @provide
    def get_client_answers_use_case(
        self,
        answer_repo: ClientAnswerRepository,
    ) -> GetClientAnswersUseCase:
        return GetClientAnswersUseCase(
            answer_repo=answer_repo,
        )

    @provide
    def update_trainer_reminder_settings_use_case(
        self,
        trainer_reminder_settings_repo: TrainerReminderSettingsRepository,
        transaction_manager: TransactionManager
    ) -> UpdateTrainerReminderSettingsUseCase:
        return UpdateTrainerReminderSettingsUseCase(
            settings_repo=trainer_reminder_settings_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_trainer_reminder_settings_use_case(
        self,
        trainer_reminder_settings_repo: TrainerReminderSettingsRepository,
    ) -> GetTrainerReminderSettingsUseCase:
        return GetTrainerReminderSettingsUseCase(
            settings_repo=trainer_reminder_settings_repo,
        )

    @provide
    def mark_booking_completed_use_case(
        self,
        booking_repo: BookingRepository,
        booking_scheduler: BookingScheduler,
        transaction_manager: TransactionManager,
    ) -> MarkBookingCompletedUseCase:
        return MarkBookingCompletedUseCase(
            booking_repo=booking_repo,
            booking_scheduler=booking_scheduler,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_bookings_history_by_trainer_use_case(
        self,
        booking_repo: BookingRepository,
    ) -> GetBookingsHistoryByTrainerUseCase:
        return GetBookingsHistoryByTrainerUseCase(
            booking_repo=booking_repo,
        )

    @provide
    def get_active_recurring_bookings_by_client_use_case(
        self,
        recurring_repo: RecurringBookingRepository,
    ) -> GetActiveRecurringBookingsByClientUseCase:
        return GetActiveRecurringBookingsByClientUseCase(
            recurring_repo=recurring_repo,
        )

    @provide
    def create_program_request_use_case(
        self,
        program_repo: ProgramRequestRepository,
        trainer_repo: TrainerRepository,
        client_repo: ClientRepository,
        notification_service: NotificationService,
        transaction_manager: TransactionManager,
    ) -> CreateProgramRequestUseCase:
        return CreateProgramRequestUseCase(
            program_repo=program_repo,
            trainer_repo=trainer_repo,
            client_repo=client_repo,
            notification_service=notification_service,
            transaction_manager=transaction_manager,
        )

    @provide
    def create_consultation_request_use_case(
        self,
        consultation_repo: ConsultationRequestRepository,
        trainer_repo: TrainerRepository,
        client_repo: ClientRepository,
        notification_service: NotificationService,
        transaction_manager: TransactionManager,
    ) -> CreateConsultationRequestUseCase:
        return CreateConsultationRequestUseCase(
            consultation_repo=consultation_repo,
            trainer_repo=trainer_repo,
            client_repo=client_repo,
            notification_service=notification_service,
            transaction_manager=transaction_manager,
        )

    @provide
    def create_feedback_use_case(
        self,
        feedback_repo: FeedbackRepository,
        trainer_repo: TrainerRepository,
        client_repo: ClientRepository,
        notification_service: NotificationService,
        transaction_manager: TransactionManager,
    ) -> CreateFeedbackUseCase:
        return CreateFeedbackUseCase(
            feedback_repo=feedback_repo,
            trainer_repo=trainer_repo,
            client_repo=client_repo,
            notification_service=notification_service,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_client_requests_by_trainer_use_case(
        self,
        program_repo: ProgramRequestRepository,
        consultation_repo: ConsultationRequestRepository,
        feedback_repo: FeedbackRepository,
    ) -> GetClientRequestsByTrainerUseCase:
        return GetClientRequestsByTrainerUseCase(
            program_repo=program_repo,
            consultation_repo=consultation_repo,
            feedback_repo=feedback_repo,
        )

    @provide
    def get_client_request_by_id_use_case(
        self,
        program_repo: ProgramRequestRepository,
        consultation_repo: ConsultationRequestRepository,
        feedback_repo: FeedbackRepository,
    ) -> GetClientRequestByIdUseCase:
        return GetClientRequestByIdUseCase(
            program_repo=program_repo,
            consultation_repo=consultation_repo,
            feedback_repo=feedback_repo,
        )

    @provide
    def update_client_request_status_use_case(
        self,
        get_request_use_case: GetClientRequestByIdUseCase,
        transaction_manager: TransactionManager,
    ) -> UpdateClientRequestStatusUseCase:
        return UpdateClientRequestStatusUseCase(
            get_request_use_case=get_request_use_case,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_active_faq_items_use_case(
        self,
        faq_repo: FaqRepository,
    ) -> GetActiveFaqItemsUseCase:
        return GetActiveFaqItemsUseCase(
            faq_repo=faq_repo,
        )

    @provide
    def get_faq_item_by_id_use_case(
        self,
        faq_repo: FaqRepository,
    ) -> GetFaqItemByIdUseCase:
        return GetFaqItemByIdUseCase(
            faq_repo=faq_repo,
        )

    @provide
    def add_faq_item_use_case(
        self,
        faq_repo: FaqRepository,
        transaction_manager: TransactionManager,
    ) -> AddFaqItemUseCase:
        return AddFaqItemUseCase(
            faq_repo=faq_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def deactivate_faq_item_use_case(
        self,
        faq_repo: FaqRepository,
        transaction_manager: TransactionManager,
    ) -> DeactivateFaqItemUseCase:
        return DeactivateFaqItemUseCase(
            faq_repo=faq_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def set_slot_blocked_use_case(
        self,
        calendar_service: CalendarService,
        transaction_manager: TransactionManager,
    ) -> SetSlotBlockedUseCase:
        return SetSlotBlockedUseCase(
            calendar_service=calendar_service,
            transaction_manager=transaction_manager,
        )

    @provide
    def set_day_blocked_use_case(
        self,
        calendar_service: CalendarService,
        transaction_manager: TransactionManager,
    ) -> SetDayBlockedUseCase:
        return SetDayBlockedUseCase(
            calendar_service=calendar_service,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_upcoming_bookings_by_client_use_case(
        self,
        booking_repo: BookingRepository,
    ) -> GetUpcomingBookingsByClientUseCase:
        return GetUpcomingBookingsByClientUseCase(
            booking_repo=booking_repo,
        )

    @provide
    def update_client_answers_use_case(
        self,
        answer_repo: ClientAnswerRepository,
        transaction_manager: TransactionManager,
    ) -> UpdateClientAnswersUseCase:
        return UpdateClientAnswersUseCase(
            answer_repo=answer_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def send_plan_next_training_reminder_use_case(
        self,
        booking_repo: BookingRepository,
        slot_repo: CalendarSlotRepository,
        client_repo: ClientRepository,
        trainer_repo: TrainerRepository,
        recurring_repo: RecurringBookingRepository,
        notification_service: NotificationService,
    ) -> SendPlanNextTrainingReminderUseCase:
        return SendPlanNextTrainingReminderUseCase(
            booking_repo=booking_repo,
            slot_repo=slot_repo,
            client_repo=client_repo,
            trainer_repo=trainer_repo,
            recurring_repo=recurring_repo,
            notification_service=notification_service,
        )

    @provide
    def grant_subscription_use_case(
        self,
        trainer_repo: TrainerRepository,
        subscription_repo: TrainerSubscriptionRepository,
        price_plan_repo: SubscriptionPricePlanRepository,
        notification_service: NotificationService,
        transaction_manager: TransactionManager,
    ) -> GrantSubscriptionUseCase:
        return GrantSubscriptionUseCase(
            trainer_repo=trainer_repo,
            subscription_repo=subscription_repo,
            price_plan_repo=price_plan_repo,
            notification_service=notification_service,
            transaction_manager=transaction_manager,
        )

    @provide
    def check_expiring_subscriptions_use_case(
        self,
        subscription_repo: TrainerSubscriptionRepository,
        trainer_repo: TrainerRepository,
        notification_service: NotificationService,
        transaction_manager: TransactionManager,
    ) -> CheckExpiringSubscriptionsUseCase:
        return CheckExpiringSubscriptionsUseCase(
            subscription_repo=subscription_repo,
            trainer_repo=trainer_repo,
            notification_service=notification_service,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_subscriptions_by_trainer_use_case(
        self,
        subscription_repo: TrainerSubscriptionRepository,
    ) -> GetSubscriptionsByTrainerUseCase:
        return GetSubscriptionsByTrainerUseCase(
            subscription_repo=subscription_repo,
        )

    @provide
    def get_user_access_use_case(
        self,
        trainer_repo: TrainerRepository,
        client_repo: ClientRepository,
        subscription_repo: TrainerSubscriptionRepository,
    ) -> GetUserAccessUseCase:
        return GetUserAccessUseCase(
            trainer_repo=trainer_repo,
            client_repo=client_repo,
            subscription_repo=subscription_repo,
        )

    @provide
    def set_trainer_blocked_use_case(
        self,
        trainer_repo: TrainerRepository,
        notification_service: NotificationService,
        transaction_manager: TransactionManager,
    ) -> SetTrainerBlockedUseCase:
        return SetTrainerBlockedUseCase(
            trainer_repo=trainer_repo,
            notification_service=notification_service,
            transaction_manager=transaction_manager,
        )

    @provide
    def set_client_blocked_use_case(
        self,
        client_repo: ClientRepository,
        transaction_manager: TransactionManager,
    ) -> SetClientBlockedUseCase:
        return SetClientBlockedUseCase(
            client_repo=client_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def search_clients_use_case(
        self,
        client_repo: ClientRepository,
    ) -> SearchClientsUseCase:
        return SearchClientsUseCase(
            client_repo=client_repo,
        )

    @provide
    def get_all_trainers_use_case(
        self,
        trainer_repo: TrainerRepository,
    ) -> GetAllTrainersUseCase:
        return GetAllTrainersUseCase(
            trainer_repo=trainer_repo,
        )

    @provide
    def get_admin_overview_stats_use_case(
        self,
        trainer_repo: TrainerRepository,
        client_repo: ClientRepository,
        booking_repo: BookingRepository,
        recurring_repo: RecurringBookingRepository,
        subscription_repo: TrainerSubscriptionRepository,
        program_repo: ProgramRequestRepository,
        consultation_repo: ConsultationRequestRepository,
        feedback_repo: FeedbackRepository,
        payment_repo: PaymentRepository,
    ) -> GetAdminOverviewStatsUseCase:
        return GetAdminOverviewStatsUseCase(
            trainer_repo=trainer_repo,
            client_repo=client_repo,
            booking_repo=booking_repo,
            recurring_repo=recurring_repo,
            subscription_repo=subscription_repo,
            program_repo=program_repo,
            consultation_repo=consultation_repo,
            feedback_repo=feedback_repo,
            payment_repo=payment_repo,
        )

    @provide
    def get_admin_trainer_report_use_case(
        self,
        trainer_repo: TrainerRepository,
        client_repo: ClientRepository,
        booking_repo: BookingRepository,
        recurring_repo: RecurringBookingRepository,
        subscription_repo: TrainerSubscriptionRepository,
        program_repo: ProgramRequestRepository,
        consultation_repo: ConsultationRequestRepository,
        feedback_repo: FeedbackRepository,
    ) -> GetAdminTrainerReportUseCase:
        return GetAdminTrainerReportUseCase(
            trainer_repo=trainer_repo,
            client_repo=client_repo,
            booking_repo=booking_repo,
            recurring_repo=recurring_repo,
            subscription_repo=subscription_repo,
            program_repo=program_repo,
            consultation_repo=consultation_repo,
            feedback_repo=feedback_repo,
        )

    @provide
    def export_report_use_case(
        self,
        trainer_repo: TrainerRepository,
        client_repo: ClientRepository,
        booking_repo: BookingRepository,
        slot_repo: CalendarSlotRepository,
        subscription_repo: TrainerSubscriptionRepository,
    ) -> ExportReportUseCase:
        return ExportReportUseCase(
            trainer_repo=trainer_repo,
            client_repo=client_repo,
            booking_repo=booking_repo,
            slot_repo=slot_repo,
            subscription_repo=subscription_repo,
        )

    @provide
    def enqueue_mailing_use_case(
        self,
        task_queue: TaskQueue,
    ) -> EnqueueMailingUseCase:
        return EnqueueMailingUseCase(
            task_queue=task_queue,
        )

    @provide
    def execute_mailing_use_case(
        self,
        trainer_repo: TrainerRepository,
        client_repo: ClientRepository,
        notification_service: NotificationService,
        task_queue: TaskQueue,
    ) -> ExecuteMailingUseCase:
        return ExecuteMailingUseCase(
            trainer_repo=trainer_repo,
            client_repo=client_repo,
            notification_service=notification_service,
            task_queue=task_queue,
        )

    @provide
    def execute_mailing_batch_use_case(
        self,
        notification_service: NotificationService,
        progress_store: MailingProgressStore,
    ) -> ExecuteMailingBatchUseCase:
        return ExecuteMailingBatchUseCase(
            notification_service=notification_service,
            progress_store=progress_store,
        )

    @provide
    def is_trainer_available_use_case(
        self,
        trainer_repo: TrainerRepository,
        subscription_repo: TrainerSubscriptionRepository,
    ) -> IsTrainerAvailableUseCase:
        return IsTrainerAvailableUseCase(
            trainer_repo=trainer_repo,
            subscription_repo=subscription_repo,
        )

    @provide
    def create_subscription_payment_use_case(
        self,
        trainer_repo: TrainerRepository,
        price_plan_repo: SubscriptionPricePlanRepository,
        payment_repo: PaymentRepository,
        provider_registry: PaymentProviderRegistry,
        confirm_use_case: ConfirmPaymentUseCase,
        notification_service: NotificationService,
        transaction_manager: TransactionManager,
    ) -> CreateSubscriptionPaymentUseCase:
        return CreateSubscriptionPaymentUseCase(
            trainer_repo=trainer_repo,
            price_plan_repo=price_plan_repo,
            payment_repo=payment_repo,
            provider_registry=provider_registry,
            confirm_use_case=confirm_use_case,
            notification_service=notification_service,
            transaction_manager=transaction_manager,
        )

    @provide
    def confirm_payment_use_case(
        self,
        payment_repo: PaymentRepository,
        price_plan_repo: SubscriptionPricePlanRepository,
        subscription_repo: TrainerSubscriptionRepository,
        trainer_repo: TrainerRepository,
        notification_service: NotificationService,
        transaction_manager: TransactionManager,
    ) -> ConfirmPaymentUseCase:
        return ConfirmPaymentUseCase(
            payment_repo=payment_repo,
            price_plan_repo=price_plan_repo,
            subscription_repo=subscription_repo,
            trainer_repo=trainer_repo,
            notification_service=notification_service,
            transaction_manager=transaction_manager,
        )

    @provide
    def reject_payment_use_case(
        self,
        payment_repo: PaymentRepository,
        trainer_repo: TrainerRepository,
        notification_service: NotificationService,
        transaction_manager: TransactionManager,
    ) -> RejectPaymentUseCase:
        return RejectPaymentUseCase(
            payment_repo=payment_repo,
            trainer_repo=trainer_repo,
            notification_service=notification_service,
            transaction_manager=transaction_manager,
        )

    @provide
    def get_payment_methods_use_case(
        self,
        provider_registry: PaymentProviderRegistry,
    ) -> GetPaymentMethodsUseCase:
        return GetPaymentMethodsUseCase(
            provider_registry=provider_registry,
        )

    @provide
    def get_payment_by_external_id_use_case(
        self,
        payment_repo: PaymentRepository,
    ) -> GetPaymentByExternalIdUseCase:
        return GetPaymentByExternalIdUseCase(
            payment_repo=payment_repo,
        )

    @provide
    def get_admin_analytics_use_case(
        self,
        bot_user_repo: BotUserRepository,
        trainer_repo: TrainerRepository,
        client_repo: ClientRepository,
        subscription_repo: TrainerSubscriptionRepository,
        booking_repo: BookingRepository,
    ) -> GetAdminAnalyticsUseCase:
        return GetAdminAnalyticsUseCase(
            bot_user_repo=bot_user_repo,
            trainer_repo=trainer_repo,
            client_repo=client_repo,
            subscription_repo=subscription_repo,
            booking_repo=booking_repo,
        )

    @provide
    def track_user_activity_use_case(
        self,
        bot_user_repo: BotUserRepository,
        transaction_manager: TransactionManager,
    ) -> TrackUserActivityUseCase:
        return TrackUserActivityUseCase(
            bot_user_repo=bot_user_repo,
            transaction_manager=transaction_manager,
        )

    @provide
    def set_bot_blocked_by_user_use_case(
        self,
        bot_user_repo: BotUserRepository,
        transaction_manager: TransactionManager,
    ) -> SetBotBlockedByUserUseCase:
        return SetBotBlockedByUserUseCase(
            bot_user_repo=bot_user_repo,
            transaction_manager=transaction_manager,
        )
