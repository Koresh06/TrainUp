from decimal import Decimal

from src.domain.entities.subscription_price_plan import SubscriptionPricePlan
from src.domain.enums.subscription import SubscriptionPlan

SUBSCRIPTION_PLAN_LABELS: dict[SubscriptionPlan, str] = {
    SubscriptionPlan.ONE_MONTH: "1 месяц",
    SubscriptionPlan.THREE_MONTHS: "3 месяца",
    SubscriptionPlan.SIX_MONTHS: "6 месяцев",
    SubscriptionPlan.TWELVE_MONTHS: "12 месяцев",
    SubscriptionPlan.INFINITE: "бессрочно",
    SubscriptionPlan.CUSTOM: "произвольный срок",
}


def usd(amount: Decimal) -> str:
    return f"${amount:,.2f}".replace(",", " ").replace(".00", "")


def plan_description(plan: SubscriptionPricePlan) -> str:
    return f"Подписка TrainUp: {SUBSCRIPTION_PLAN_LABELS.get(plan.plan, plan.plan.value)}"
