from enum import Enum


class SubscriptionPlan(Enum):
    ONE_MONTH = "one_month"
    THREE_MONTHS = "three_months"
    SIX_MONTHS = "six_months"
    TWELVE_MONTHS = "twelve_months"
    INFINITE = "infinite"


class SubscriptionStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"