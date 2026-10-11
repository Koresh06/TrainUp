from html import escape

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.admin.get_overview_stats import (
    AdminOverviewStatsDTO,
    GetAdminOverviewStatsRequest,
)
from src.application.use_cases.stats.period import STATS_PERIOD_LABELS
from src.presentation.telegram.features.admin.common import (
    current_admin_period,
    money,
    percent,
    progress_bar,
)
from src.presentation.telegram.features.trainer.stats.helper import period_flags

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
