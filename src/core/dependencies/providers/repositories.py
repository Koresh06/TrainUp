from dishka import Provider, provide, Scope
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repositories.client import ClientRepository
from src.domain.repositories.subscription_price_plan import SubscriptionPricePlanRepository
from src.domain.repositories.trainer import TrainerRepository
from src.domain.repositories.booking import BookingRepository
from src.domain.repositories.program import ProgramRequestRepository
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.consultation import ConsultationRequestRepository
from src.domain.repositories.invite_link import TrainerInviteLinkRepository
from src.domain.repositories.feedback import FeedbackRepository
from src.domain.repositories.faq import FaqRepository
from src.domain.repositories.slot_template import SlotTemplateRepository
from src.infrastructure.repositories.client.sqlalchemy import SQLAlchemyClientRepo
from src.infrastructure.repositories.subscription_price_plan.sqlalchemy import SQLAlchemySubscriptionPricePlanRepo
from src.infrastructure.repositories.trainer.sqlalchemy import SQLAlchemyTrainerRepo
from src.infrastructure.repositories.booking.sqlalchemy import SQLAlchemyBookingRepo
from src.infrastructure.repositories.program.sqlalchemy import SQLAlchemyProgramRequestRepo
from src.infrastructure.repositories.subscription.sqlalchemy import SQLAlchemyTrainerSubscriptionRepo
from src.infrastructure.repositories.calendar_slot.sqlalchemy import SQLAlchemyCalendarSlotRepo
from src.infrastructure.repositories.consultation.sqlalchemy import SQLAlchemyConsultationRequestRepo
from src.infrastructure.repositories.invite_link.sqlalchemy import SQLAlchemyTrainerInviteLinkRepo
from src.infrastructure.repositories.feedback.sqlalchemy import SQLAlchemyFeedbackRepo
from src.infrastructure.repositories.faq.sqlalchemy import SQLAlchemyFaqRepo
from src.infrastructure.repositories.slot_template.sqlalchemy import SQLAlchemySlotTemplateRepo


class RepositoriesProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_client_repository(self, session: AsyncSession) -> ClientRepository:
        return SQLAlchemyClientRepo(session=session)

    @provide(scope=Scope.REQUEST)
    def get_trainer_repository(self, session: AsyncSession) -> TrainerRepository:
        return SQLAlchemyTrainerRepo(session=session)

    @provide(scope=Scope.REQUEST)
    def get_booking_repository(self, session: AsyncSession) -> BookingRepository:
        return SQLAlchemyBookingRepo(session=session)

    @provide(scope=Scope.REQUEST)
    def get_program_request_repository(self, session: AsyncSession) -> ProgramRequestRepository:
        return SQLAlchemyProgramRequestRepo(session=session)

    @provide(scope=Scope.REQUEST)
    def get_trainer_subscription_repository(self, session: AsyncSession) -> TrainerSubscriptionRepository:
        return SQLAlchemyTrainerSubscriptionRepo(session=session)

    @provide(scope=Scope.REQUEST)
    def get_calendar_slot_repository(self, session: AsyncSession) -> CalendarSlotRepository:
        return SQLAlchemyCalendarSlotRepo(session=session)

    @provide(scope=Scope.REQUEST)
    def get_consultation_request_repository(self, session: AsyncSession) -> ConsultationRequestRepository:
        return SQLAlchemyConsultationRequestRepo(session=session)

    @provide(scope=Scope.REQUEST)
    def get_trainer_invite_link_repository(self, session: AsyncSession) -> TrainerInviteLinkRepository:
        return SQLAlchemyTrainerInviteLinkRepo(session=session)

    @provide(scope=Scope.REQUEST)
    def get_feedback_repository(self, session: AsyncSession) -> FeedbackRepository:
        return SQLAlchemyFeedbackRepo(session=session)

    @provide(scope=Scope.REQUEST)
    def get_faq_repository(self, session: AsyncSession) -> FaqRepository:
        return SQLAlchemyFaqRepo(session=session)

    @provide(scope=Scope.REQUEST)
    def get_slot_template_repository(self, session: AsyncSession) -> SlotTemplateRepository:
        return SQLAlchemySlotTemplateRepo(session=session)

    @provide(scope=Scope.REQUEST)
    def get_subcriiption_price_plan_repository(self, session: AsyncSession) -> SubscriptionPricePlanRepository:
        return SQLAlchemySubscriptionPricePlanRepo(session=session)