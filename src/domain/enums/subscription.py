from enum import Enum


class SubscriptionPlan(Enum):
    TRIAL = "trial"
    BASIC = "basic"
    PREMIUM = "premium"


class SubscriptionStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
