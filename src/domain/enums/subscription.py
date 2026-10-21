from enum import Enum


class SubscriptionPlan(Enum):
    ONE_MONTH = "one_month"
    THREE_MONTHS = "three_months"
    SIX_MONTHS = "six_months"
    TWELVE_MONTHS = "twelve_months"
    INFINITE = "infinite"
    CUSTOM = "custom"  # произвольный срок в днях — выдаёт админ (пробный период и т.п.)


class SubscriptionStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SubscriptionSource(Enum):
    PURCHASE = "purchase"  # оплата в боте
    CASH = "cash"          # оплатил наличными/переводом — подписку выдал админ
    TRIAL = "trial"        # бесплатно: пробный/тестовый период от админа
    REFERRAL = "referral"  # бесплатно: бонус за приглашённого тренера


PAID_SUBSCRIPTION_SOURCES = (SubscriptionSource.PURCHASE, SubscriptionSource.CASH)
