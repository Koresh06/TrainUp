from pydantic_settings import BaseSettings


class BusinessSettings(BaseSettings):
    """
    Параметры бизнес-логики, которые отличаются между тестом и продом или
    которые заказчик может захотеть поменять без релиза. Читаются из .env
    (APP_CONFIG__BUSINESS__*), дефолты — боевые значения.
    """

    timezone: str = "Europe/Moscow"

    # за сколько часов до тренировки напоминание, если тренер не настроил своё
    reminder_hours_before_training: int = 2
    # ТЕСТ: напоминание через reminder_test_delay_minutes после подтверждения
    reminder_test_mode: bool = False
    reminder_test_delay_minutes: int = 1
    # ТЕСТ: cron постоянных клиентов раз в 2 минуты вместо раза в сутки
    recurring_bookings_test_mode: bool = False

    default_calendar_horizon_days: int = 14
    default_max_active_bookings: int = 1
    calendar_buffer_days: int = 60

    plan_next_training_reminder_days: int = 3

    # за сколько часов до окончания подписки предупреждать тренера (по убыванию)
    subscription_warning_hours: list[int] = [48, 3]
