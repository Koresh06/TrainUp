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

    # бесплатный пробный период новому тренеру сразу после регистрации (0 — выключен)
    trainer_trial_days: int = 7

    # во сколько (по времени проекта) тренеру приходит сводка «сегодня у вас…»,
    # если он не настроил своё время
    morning_digest_hour: int = 8

    # через сколько дней без тренировок клиент попадает в «😴 Давно не были»
    inactive_client_days: int = 21

    # реферальная программа тренеров: +дни подписки пригласившему после первой
    # оплаты приглашённого и +дни к пробному периоду приглашённому (0 — без бонуса)
    trainer_referral_bonus_days: int = 30
    trainer_referral_friend_days: int = 7
