from dishka import Provider, Scope, provide

from src.domain.repositories.calendar_slot import CalendarSlotRepository
from src.domain.repositories.slot_template import SlotTemplateRepository
from src.domain.services.calendar_service import CalendarService


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
