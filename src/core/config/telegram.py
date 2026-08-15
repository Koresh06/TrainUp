from pydantic_settings import BaseSettings


class TelegramSettings(BaseSettings):
    bot_token: str = "your_bot_token"
    bot_username: str = "your_bot_username"
    admin_ids: list[int] = [123456789]
    bot_proxy: str | None = None