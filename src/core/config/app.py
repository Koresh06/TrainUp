from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    name: str = "APP_NAME"
    debug: bool = False
    # уровень логов приложения: DEBUG / INFO / WARNING
    log_level: str = "INFO"
    # каталог файлов логов (ротация); пусто — только консоль
    log_dir: str | None = "logs"
    sentry_dsn: str | None = None
    hold_slots_time: int = 300
    pre_publication_window_hours: int = 2