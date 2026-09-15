from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.stats.get_trainer import (
    GetTrainerStatsRequest,
    TrainerStatsDTO,
)
from src.application.use_cases.stats.get_trainer import StatsPeriod

from .helper import ScopePrivate, current_period, period_flags


PERIOD_LABELS: dict[StatsPeriod, str] = {
    StatsPeriod.TODAY: "Сегодня",
    StatsPeriod.WEEK: "Неделя",
    StatsPeriod.MONTH: "Месяц",
    StatsPeriod.ALL: "Всё время",
}


@inject
async def stats_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    period = current_period(dialog_manager, ScopePrivate.TRAINER)

    stats: TrainerStatsDTO = await mediator.handle(
        GetTrainerStatsRequest(trainer_id=trainer_id, period=period)
    )

    return {
        **period_flags(period),
        "total_clients": stats.total_clients,
        "completed_trainings": stats.completed_trainings,
        "cancelled_bookings": stats.cancelled_bookings,
        "upcoming_bookings": stats.upcoming_bookings,
        "recurring_clients": stats.recurring_clients,
    }