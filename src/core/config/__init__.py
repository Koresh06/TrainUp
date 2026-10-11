from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.config.app import AppSettings
from src.core.config.business import BusinessSettings
from src.core.config.payment import PaymentSettings
from src.core.config.database import DatabaseSettings
from src.core.config.telegram import TelegramSettings


class Settings(BaseSettings):
    app: AppSettings = AppSettings()
    db: DatabaseSettings = DatabaseSettings()
    telegram: TelegramSettings = TelegramSettings()
    business: BusinessSettings = BusinessSettings()
    payment: PaymentSettings = PaymentSettings()

    model_config = SettingsConfigDict(
        env_file=(".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
        # .env общий с docker compose (WEBHOOK_DOMAIN для Caddy и т.п.) —
        # ключи не для приложения не должны ронять загрузку настроек
        extra="ignore",
    )


settings = Settings()