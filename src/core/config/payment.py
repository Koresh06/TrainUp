from decimal import Decimal

from pydantic_settings import BaseSettings

# Цены подписок — в USD. Провайдеры, которые списывают в другой валюте,
# пересчитывают сумму по курсу отсюда (меняется в .env без релиза).


class YooKassaSettings(BaseSettings):
    enabled: bool = False
    account_id: int = 0
    secret_key: str = ""
    # куда ЮKassa вернёт пользователя после оплаты (страница webhook-сервиса)
    return_url: str = ""
    usd_to_rub_rate: Decimal = Decimal("90")
    # прокси только для запросов к API ЮKassa; пусто — напрямую
    proxy: str = ""


class TelegramStarsSettings(BaseSettings):
    enabled: bool = False
    # сколько долларов стоит 1 звезда при оплате (Telegram продаёт ~0.013–0.02 $)
    usd_per_star: Decimal = Decimal("0.02")


class ManualPaymentSettings(BaseSettings):
    enabled: bool = True
    # контакт для связи: @username или телефон администратора
    admin_contact: str = ""


class PaymentSettings(BaseSettings):
    yookassa: YooKassaSettings = YooKassaSettings()
    telegram_stars: TelegramStarsSettings = TelegramStarsSettings()
    manual: ManualPaymentSettings = ManualPaymentSettings()
    # ТОЛЬКО для разработки: способ «🧪 Тестовая оплата», подтверждается сразу
    test_mode: bool = False
