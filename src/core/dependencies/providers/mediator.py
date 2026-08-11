from dishka import Provider, provide, Scope

from src.application.mediator import Mediator
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
from src.application.use_cases.invite_link.resolve import ResolveInviteLinkRequest, ResolveInviteLinkUseCase
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdRequest, GetTrainerByIdUseCase


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

        return mediator

