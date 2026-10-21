from html import escape

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.stats.get_trainer import (
    GetTrainerStatsRequest,
    TrainerStatsDTO,
)
from src.application.use_cases.stats.period import STATS_PERIOD_LABELS
from src.domain.utils import get_project_today
from src.presentation.telegram.charts import render
from src.presentation.telegram.charts.media import chart_media
from src.presentation.telegram.charts.text import (
    byn,
    chart_period_label,
    hours_label,
    weekdays_label,
)

from .helper import (
    ScopePrivate,
    TrainerChart,
    chart_flags,
    current_chart,
    current_period,
    period_flags,
)

MEDALS = ["🥇", "🥈", "🥉"]


async def _load_stats(dialog_manager: DialogManager, mediator: Mediator) -> TrainerStatsDTO:
    return await mediator.handle(
        GetTrainerStatsRequest(
            trainer_id=dialog_manager.start_data["trainer_id"],
            period=current_period(dialog_manager, ScopePrivate.TRAINER),
        )
    )


@inject
async def stats_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    s = await _load_stats(dialog_manager, mediator)

    top = "\n".join(
        f"{MEDALS[i]} {escape(c.name)} — {c.completed}" for i, c in enumerate(s.top_clients)
    ) or "—"
    busiest = (
        f"🔥 <b>Пиковое время:</b> {weekdays_label(s.busiest_weekdays)} · "
        f"{hours_label(s.busiest_hours)}\n\n"
        if s.busiest_weekdays
        else ""
    )

    text = (
        f"📊 <b>Статистика · {STATS_PERIOD_LABELS[s.period]}</b>\n\n"
        f"👥 <b>Клиенты</b>\n"
        f"├ Всего: <b>{s.total_clients}</b> (+{s.new_clients} новых)\n"
        f"├ Ходили на тренировки: {s.active_clients}\n"
        f"└ Постоянных: {s.recurring_clients}\n\n"
        f"🏋 <b>Тренировки</b>\n"
        f"├ Проведено: <b>{s.completed_trainings}</b>\n"
        f"├ Не пришли: {s.no_show_trainings}\n"
        f"├ Запланировано до конца периода: {s.planned_trainings}\n"
        f"├ Отменено: {s.cancelled_bookings} (доля отмен {s.cancel_rate:.0%})\n"
        f"└ Всего предстоящих: {s.upcoming_bookings}\n\n"
        f"💰 <b>Доход</b> <i>(по проведённым)</i>\n"
        f"├ За период: <b>{byn(s.income)}</b>\n"
        f"├ Средний чек: {byn(s.average_check)}\n"
        f"└ Ожидается по записям: {byn(s.expected_income)}\n\n"
        f"{busiest}"
        f"📨 Заявок от клиентов: {s.requests_count}\n\n"
        f"🏆 <b>Самые активные клиенты</b>\n{top}"
    )
    return {"stats_text": text, **period_flags(s.period)}


@inject
async def stats_chart_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    s = await _load_stats(dialog_manager, mediator)
    chart = current_chart(dialog_manager)
    series = s.series
    rng = series.range
    when = chart_period_label(s.period, rng)
    today = get_project_today()

    if chart == TrainerChart.INCOME:
        total = sum(series.income)
        caption = f"💰 <b>Доход</b> · {when}\nИтого {byn(total)} · средний чек {byn(s.average_check)}"

        def draw() -> bytes:
            if not total:
                return render.empty_chart(title="Доход", subtitle=when)
            return render.stacked_bars(
                title="Доход", subtitle=f"{when} · итого {byn(total)}",
                buckets=series.buckets, by_month=rng.by_month, today=today, money="BYN",
                series=[render.Series("Доход", series.income, render.AQUA)],
            )
    elif chart == TrainerChart.LOAD:
        caption = (
            f"🗓 <b>Загрузка по дням и часам</b> · {STATS_PERIOD_LABELS[s.period].lower()}\n"
            f"Пик: {weekdays_label(s.busiest_weekdays)} · {hours_label(s.busiest_hours)}"
        )

        def draw() -> bytes:
            if not any(any(row) for row in series.load):
                return render.empty_chart(title="Загрузка по дням и часам", subtitle=when)
            return render.weekly_heatmap(
                title="Загрузка по дням и часам",
                subtitle="Проведённые и запланированные занятия · чем темнее, тем плотнее",
                load=series.load,
            )
    else:
        completed, planned, cancelled = (
            sum(series.completed), sum(series.planned), sum(series.cancelled)
        )
        caption = (
            f"🏋 <b>Тренировки</b> · {when}\n"
            f"Проведено {completed} · запланировано {planned} · отменено {cancelled}"
        )

        def draw() -> bytes:
            if not completed + planned + cancelled:
                return render.empty_chart(title="Тренировки", subtitle=when)
            return render.stacked_bars(
                title="Тренировки",
                subtitle=f"{when} · проведено {completed} · запланировано {planned}",
                buckets=series.buckets, by_month=rng.by_month, today=today,
                series=[
                    render.Series("Проведено", series.completed, render.BLUE),
                    render.Series("Запланировано", series.planned, render.BLUE_LIGHT),
                    render.Series("Отменено", series.cancelled, render.RED),
                ],
            )

    return {
        "chart": await chart_media(draw),
        "caption": caption,
        **period_flags(s.period),
        **chart_flags(chart),
    }
