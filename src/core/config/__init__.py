from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.config.app import AppSettings
from src.core.config.database import DatabaseSettings
from src.core.config.telegram import TelegramSettings


class Settings(BaseSettings):
    app: AppSettings = AppSettings()
    db: DatabaseSettings = DatabaseSettings()
    telegram: TelegramSettings = TelegramSettings()
    # payment: PaymentSettings = PaymentSettings()

    model_config = SettingsConfigDict(
        env_file=(".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )


settings = Settings()