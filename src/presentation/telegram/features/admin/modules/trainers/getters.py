from datetime import datetime, timezone
from html import escape

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.admin.get_trainer_report import (
    AdminTrainerReportDTO,
    GetAdminTrainerReportRequest,
)
from src.application.use_cases.stats.period import STATS_PERIOD_LABELS
from src.application.use_cases.subscription.get_active import GetActiveSubscriptionRequest
from src.application.use_cases.subscription.get_active_price_plans import (
    GetActivePricePlansRequest,
)
from src.application.use_cases.trainer.get_all import GetAllTrainersRequest
from src.domain.entities.subscription_price_plan import SubscriptionPricePlan
from src.domain.entities.trainer import Trainer
from src.domain.entities.trainer_subscription import TrainerSubscription
from src.domain.enums.subscription import SubscriptionSource
from src.presentation.telegram.features.admin.common import current_admin_period, money
from src.presentation.telegram.features.trainer.register.getters import PLAN_LABELS
from src.presentation.telegram.features.trainer.stats.helper import period_flags
from src.utils.timezone import to_moscow

SOURCE_LABELS: dict[SubscriptionSource, str] = {
    SubscriptionSource.PURCHASE: "оплата в боте",
    SubscriptionSource.CASH: "наличные/перевод",
    SubscriptionSource.TRIAL: "бесплатно",
}

GRANT_DAYS_OPTIONS = [3, 7, 14, 30, 90]


def _date(dt: datetime) -> str:
    return to_moscow(dt).strftime("%d.%m.%Y")


@inject
async def admin_trainers_list_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainers: list[Trainer] = await mediator.handle(GetAllTrainersRequest())
    items = []
    for trainer in trainers:
        subscription: TrainerSubscription | None = await mediator.handle(
            GetActiveSubscriptionRequest(trainer_id=trainer.id)
        )
        if not trainer.is_active:
            icon, until = "⛔", "заблокирован"
        elif subscription is not None:
            icon, until = "✅", f"до {_date(subscription.expired_at)}"
        else:
            icon, until = "⌛", "нет подписки"
        items.append({"id": str(trainer.id), "label": f"{icon} {trainer.name} · {until}"})

    return {
        "trainers": items,
        "empty_hint": "" if items else "\n\nТренеров пока нет.",
    }


@inject
async def admin_trainer_card_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    period = current_admin_period(dialog_manager)
    r: AdminTrainerReportDTO = await mediator.handle(
        GetAdminTrainerReportRequest(
            trainer_id=dialog_manager.dialog_data["trainer_id"], period=period
        )
    )
    t = r.trainer
    if r.subscription is not None:
        left_days = max((r.subscription.expired_at - datetime.now(timezone.utc)).days, 0)
        subscription_line = (
            f"✅ до {_date(r.subscription.expired_at)} (осталось {left_days} дн., "
            f"{SOURCE_LABELS[r.subscription.source]})"
        )
    else:
        subscription_line = "⌛ нет активной подписки"

    text = (
        f"👨‍🏫 <b>{escape(t.name)}</b>{'  ⛔ заблокирован' if not t.is_active else ''}\n"
        f'💬 <a href="tg://user?id={t.tg_id}">написать</a> · 📞 {t.phone or "—"}\n'
        f"🗓 В боте с {_date(t.created_at)}\n\n"
        f"💳 <b>Подписка:</b> {subscription_line}\n"
        f"💰 Оплачено всего: <b>{money(r.paid_total)}</b> ({r.payments_count} опл.)\n\n"
        f"📊 <b>{STATS_PERIOD_LABELS[period]}</b>\n"
        f"├ Клиентов: <b>{r.clients_total}</b> (+{r.clients_new})\n"
        f"├ Постоянных: {r.recurring_clients}\n"
        f"├ Тренировок проведено: <b>{r.trainings_completed}</b>\n"
        f"├ Запланировано: {r.trainings_active}\n"
        f"├ Отменено: {r.trainings_cancelled}\n"
        f"└ Заявок: {r.requests_total}"
    )
    return {
        "card_text": text,
        "is_blocked": not t.is_active,
        "is_active": t.is_active,
        **period_flags(period),
    }


@inject
async def admin_grant_plans_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    plans: list[SubscriptionPricePlan] = await mediator.handle(GetActivePricePlansRequest())
    return {
        "plans": [
            {"id": str(p.id), "label": f"{PLAN_LABELS.get(p.plan, p.plan.value)} — {money(p.price)}"}
            for p in plans
        ]
    }


async def admin_grant_days_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    return {"days": [{"id": str(d), "label": f"{d} дн."} for d in GRANT_DAYS_OPTIONS]}


@inject
async def admin_grant_confirm_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    data = dialog_manager.dialog_data
    if data.get("grant_plan_id"):
        plans: list[SubscriptionPricePlan] = await mediator.handle(GetActivePricePlansRequest())
        plan = next(p for p in plans if p.id == data["grant_plan_id"])
        what = (
            f"💵 Оплата наличными/переводом\n"
            f"Тариф: {PLAN_LABELS.get(plan.plan, plan.plan.value)}, сумма {money(plan.price)}"
        )
    else:
        what = f"🎁 Бесплатный период: {data['grant_days']} дн."
    return {"grant_summary": what, "trainer_name": escape(data.get("trainer_name", ""))}


async def admin_trainer_name_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    return {"trainer_name": escape(dialog_manager.dialog_data.get("trainer_name", ""))}
