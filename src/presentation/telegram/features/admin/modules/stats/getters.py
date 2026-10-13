from enum import Enum
from html import escape

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.admin.get_overview_stats import (
    AdminOverviewStatsDTO,
    GetAdminOverviewStatsRequest,
)
from src.application.use_cases.admin.get_analytics import (
    AdminAnalyticsDTO,
    GetAdminAnalyticsRequest,
)
from src.application.use_cases.stats.period import STATS_PERIOD_LABELS
from src.domain.utils import get_project_today
from src.presentation.telegram.charts import render
from src.presentation.telegram.charts.media import chart_media
from src.presentation.telegram.charts.text import chart_period_label
from src.presentation.telegram.features.admin.common import (
    current_admin_period,
    money,
    percent,
    progress_bar,
)
from src.presentation.telegram.features.trainer.stats.helper import (
    chart_flags,
    current_chart,
    period_flags,
)

MEDALS = ["🥇", "🥈", "🥉", "4.", "5."]


@inject
async def admin_stats_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    period = current_admin_period(dialog_manager)
    s: AdminOverviewStatsDTO = await mediator.handle(
        GetAdminOverviewStatsRequest(period=period)
    )

    trainings_total = s.trainings_completed + s.trainings_cancelled + s.trainings_active
    top = "\n".join(
        f"{MEDALS[i]} {escape(t.name)} — {t.completed}"
        for i, t in enumerate(s.top_trainers)
    ) or "—"

    by_method = "\n".join(
        f"│  {method.label()}: {money(total)} ({count})"
        for method, (count, total) in s.payments_by_method.items()
    )
    methods_block = f"├ По способам оплаты:\n{by_method}\n" if by_method else ""

    text = (
        f"📊 <b>Статистика · {STATS_PERIOD_LABELS[period]}</b>\n\n"
        f"👨‍🏫 <b>Тренеры</b>\n"
        f"├ Всего: <b>{s.trainers_total}</b> (+{s.trainers_new} за период)\n"
        f"├ С активной подпиской: <b>{s.trainers_with_subscription}</b>\n"
        f"│  {progress_bar(s.trainers_with_subscription, s.trainers_total)}\n"
        f"└ Заблокировано: {s.trainers_blocked}\n\n"
        f"👥 <b>Клиенты</b>\n"
        f"├ Всего: <b>{s.clients_total}</b> (+{s.clients_new} за период)\n"
        f"├ Постоянных: {s.recurring_active}\n"
        f"└ Заблокировано: {s.clients_blocked}\n\n"
        f"🏋 <b>Тренировки</b> <i>(по дате занятия)</i>\n"
        f"├ Проведено: <b>{s.trainings_completed}</b>\n"
        f"├ Запланировано: {s.trainings_active}\n"
        f"└ Отменено: {s.trainings_cancelled} "
        f"(доля отмен {percent(s.trainings_cancelled, trainings_total)})\n\n"
        f"📨 <b>Заявки</b>\n"
        f"└ Программы {s.requests_program} · Консультации {s.requests_consultation} · "
        f"Обратная связь {s.requests_feedback}\n\n"
        f"💰 <b>Оплаты подписок</b>\n"
        f"├ За период: <b>{money(s.revenue_period)}</b> ({s.payments_count} опл.)\n"
        f"│  ├ Онлайн в боте: {money(s.revenue_purchase)}\n"
        f"│  └ Через администратора: {money(s.revenue_cash)}\n"
        f"{methods_block}"
        f"├ Бесплатных периодов выдано: {s.trials_count}\n"
        f"└ За всё время: <b>{money(s.revenue_all_time)}</b>\n\n"
        f"🏆 <b>Топ тренеров по проведённым</b>\n{top}"
    )
    return {"stats_text": text, **period_flags(period)}


class AdminChart(str, Enum):
    USERS = "users"
    ACTIVITY = "activity"
    REVENUE = "revenue"
    TRAININGS = "trainings"


ADMIN_CHART_LABELS: dict[AdminChart, str] = {
    AdminChart.USERS: "👥 Новые",
    AdminChart.ACTIVITY: "🔥 Активность",
    AdminChart.REVENUE: "💰 Выручка",
    AdminChart.TRAININGS: "🏋 Занятия",
}


async def _load_analytics(dialog_manager: DialogManager, mediator: Mediator) -> AdminAnalyticsDTO:
    return await mediator.handle(
        GetAdminAnalyticsRequest(period=current_admin_period(dialog_manager))
    )


@inject
async def admin_users_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    a = await _load_analytics(dialog_manager, mediator)
    reachable = a.users_total - a.blocked_total
    text = (
        f"👥 <b>Пользователи · {STATS_PERIOD_LABELS[a.period]}</b>\n\n"
        f"📦 <b>Аудитория</b>\n"
        f"├ Всего писали боту: <b>{a.users_total}</b>\n"
        f"├ Тренеры: {a.trainers_total}\n"
        f"├ Клиенты: {a.clients_total}\n"
        f"└ Без регистрации: {a.guests_total}\n\n"
        f"🆕 <b>Новые за период: +{a.users_new}</b>\n"
        f"├ Тренеры: +{a.trainers_new}\n"
        f"├ Клиенты: +{a.clients_new}\n"
        f"└ Без регистрации: +{a.guests_new}\n\n"
        f"🔥 <b>Активность</b>\n"
        f"├ За период: <b>{a.active_period}</b>\n"
        f"├ Сегодня (DAU): {a.dau}\n"
        f"├ За 7 дней (WAU): {a.wau}\n"
        f"├ За 30 дней (MAU): {a.mau}\n"
        f"├ Вовлечённость DAU/MAU: {percent(a.dau, a.mau)}\n"
        f"└ Не заходили 30+ дней: {a.dormant}\n\n"
        f"🚫 <b>Заблокировали бота</b>\n"
        f"├ Сейчас: <b>{a.blocked_total}</b> ({percent(a.blocked_total, a.users_total)} аудитории)\n"
        f"├ За период: +{a.blocked_new}\n"
        f"├ Из них тренеров: {a.blocked_trainers}, клиентов: {a.blocked_clients}\n"
        f"└ Доступно для рассылки: {reachable}\n"
        f"   {progress_bar(reachable, a.users_total)}\n\n"
        f"🎯 <b>Тренеры: пробный период → оплата</b>\n"
        f"├ Получили пробный период: {a.trainers_trial}\n"
        f"├ Сейчас на пробном: {a.trainers_on_trial_now}\n"
        f"├ Платили хотя бы раз: {a.trainers_paid}\n"
        f"└ Конверсия пробный → оплата: <b>{percent(a.trainers_trial_to_paid, a.trainers_trial)}</b> "
        f"({a.trainers_trial_to_paid} из {a.trainers_trial})\n\n"
        f"<i>Блокировки считаются с момента запуска аналитики: Telegram сообщает о них "
        f"боту, только когда пользователь блокирует его.</i>"
    )
    return {"users_text": text, **period_flags(a.period)}


@inject
async def admin_chart_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    a = await _load_analytics(dialog_manager, mediator)
    chart = current_chart(dialog_manager, AdminChart)
    series = a.series
    rng = series.range
    when = chart_period_label(a.period, rng)
    today = get_project_today()

    def bars(title: str, subtitle: str, items: list[render.Series], money_label: str | None = None):
        def draw() -> bytes:
            if not any(float(v) for item in items for v in item.values):
                return render.empty_chart(title=title, subtitle=when)
            return render.stacked_bars(
                title=title, subtitle=subtitle, buckets=series.buckets,
                by_month=rng.by_month, series=items, today=today, money=money_label,
            )
        return draw

    if chart == AdminChart.ACTIVITY:
        # будущие дни недели/месяца — None: линия обрывается на сегодня
        active = [
            value if bucket <= rng.bucket_of(today) else None
            for bucket, value in zip(series.buckets, series.active_users)
        ]
        blocked = sum(series.blocked_bot)
        unit = "за месяц" if rng.by_month else "за день"
        caption = (
            f"🔥 <b>Активность</b> · {when}\n"
            f"Уникальные пользователи {unit} · заблокировали бота: {blocked}"
        )

        def draw() -> bytes:
            if not any(series.active_users) and not blocked:
                return render.empty_chart(title="Активность", subtitle=when)
            return render.line_with_bars(
                title="Активность",
                subtitle=f"{when} · DAU {a.dau} · WAU {a.wau} · MAU {a.mau}",
                buckets=series.buckets, by_month=rng.by_month, today=today,
                line=render.Series(f"Активные {unit}", active, render.BLUE),
                bars=render.Series("Заблокировали бота", series.blocked_bot, render.RED),
            )
    elif chart == AdminChart.REVENUE:
        total = sum(series.revenue)
        caption = f"💰 <b>Выручка с подписок</b> · {when}\nИтого {money(total)}"
        draw = bars(
            "Выручка с подписок", f"{when} · итого {money(total)}",
            [render.Series("Выручка", series.revenue, render.AQUA)], "$",
        )
    elif chart == AdminChart.TRAININGS:
        completed, planned, cancelled = (
            sum(series.trainings_completed), sum(series.trainings_planned),
            sum(series.trainings_cancelled),
        )
        caption = (
            f"🏋 <b>Занятия всех тренеров</b> · {when}\n"
            f"Проведено {completed} · запланировано {planned} · отменено {cancelled}"
        )
        draw = bars(
            "Занятия всех тренеров", f"{when} · проведено {completed} · запланировано {planned}",
            [
                render.Series("Проведено", series.trainings_completed, render.BLUE),
                render.Series("Запланировано", series.trainings_planned, render.BLUE_LIGHT),
                render.Series("Отменено", series.trainings_cancelled, render.RED),
            ],
        )
    else:
        new_total = sum(series.new_trainers) + sum(series.new_clients) + sum(series.new_guests)
        caption = (
            f"👥 <b>Новые пользователи</b> · {when}\n"
            f"+{new_total}: тренеры {sum(series.new_trainers)}, клиенты "
            f"{sum(series.new_clients)}, без регистрации {sum(series.new_guests)}"
        )
        draw = bars(
            "Новые пользователи", f"{when} · +{new_total}",
            [
                render.Series("Тренеры", series.new_trainers, render.VIOLET),
                render.Series("Клиенты", series.new_clients, render.BLUE),
                render.Series("Без регистрации", series.new_guests, render.ORANGE),
            ],
        )

    return {
        "chart": await chart_media(draw),
        "caption": caption,
        **period_flags(a.period),
        **chart_flags(chart, ADMIN_CHART_LABELS),
    }
