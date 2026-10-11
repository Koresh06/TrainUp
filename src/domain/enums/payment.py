from enum import Enum


class PaymentMethod(str, Enum):
    YOOKASSA = "yookassa"              # карта/СБП через ЮKassa (списание в RUB)
    TELEGRAM_STARS = "telegram_stars"  # Telegram Stars (XTR)
    MANUAL = "manual"                  # тренер платит админу напрямую, админ подтверждает
    TEST = "test"                      # только для разработки: оплата подтверждается сразу

    def label(self) -> str:
        match self:
            case PaymentMethod.YOOKASSA:
                return "💳 Картой (ЮKassa)"
            case PaymentMethod.TELEGRAM_STARS:
                return "⭐ Telegram Stars"
            case PaymentMethod.MANUAL:
                return "🤝 Через администратора"
            case PaymentMethod.TEST:
                return "🧪 Тестовая оплата"


class PaymentStatus(str, Enum):
    PENDING = "pending"                            # ждём оплату у провайдера
    WAITING_CONFIRMATION = "waiting_confirmation"  # ручная: ждём подтверждения админа
    PAID = "paid"
    FAILED = "failed"                              # отменён провайдером / отклонён админом


class PaymentPurpose(str, Enum):
    SUBSCRIPTION = "subscription"  # подписка тренера; purpose_id — id тарифа


# цены подписок всегда в долларах; провайдеры пересчитывают в свою валюту
PAYMENT_BASE_CURRENCY = "USD"
