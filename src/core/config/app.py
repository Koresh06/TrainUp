from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    name: str = "APP_NAME"
    debug: bool = False
    sentry_dsn: str | None = None
    hold_slots_time: int = 300
    pre_publication_window_hours: int = 2