from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from src.domain.enums.consultation import ConsultationType
from src.domain.enums.program import ProgramType
from src.domain.enums.request import ClientRequestKind, RequestStatus
from src.domain.enums.training import HealthCondition, TrainingDirection, TrainingGoal

from zoneinfo import ZoneInfo

from src.core.config import settings

# Значения, которые меняются между тестом/продом, берутся из .env
# (APP_CONFIG__BUSINESS__*, см. src/core/config/business.py)
_business = settings.business

PROJECT_TIMEZONE = ZoneInfo(_business.timezone)

# --- Слоты календаря: длительность и генерация сетки времён ---

SLOT_DURATION_MINUTES = 60  # длительность одной тренировки в минутах (используется при создании SlotTemplate)

MAX_SLOT_CAPACITY = 5  # максимум мест, которые тренер может выставить на один слот (ограничение ➖/➕ в кабинете)
TIME_SLOTS_START = time(8, 0)   # с какого времени начинается сетка выбора времени для настройки расписания
TIME_SLOTS_END = time(22, 0)    # последнее возможное время в сетке
TIME_SLOTS_STEP_MINUTES = 30    # шаг между вариантами времени в сетке (08:00, 08:30, 09:00, ...)

WEEKDAY_LABELS_FULL = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
]  # порядок соответствует Python date.weekday(): 0=Понедельник ... 6=Воскресенье

MONTHS_GENITIVE = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]


def day_label(day: date) -> str:
    """«среда 22 октября» — для уведомлений и сводок."""
    return f"{WEEKDAY_LABELS_FULL[day.weekday()].lower()} {day.day} {MONTHS_GENITIVE[day.month - 1]}"


WEEKDAY_LABELS_EVERY = [
    "по понедельникам",
    "по вторникам",
    "по средам",
    "по четвергам",
    "по пятницам",
    "по субботам",
    "по воскресеньям",
]


def generate_time_options() -> list[time]:
    """Список всех возможных времён с шагом TIME_SLOTS_STEP_MINUTES в диапазоне
    [TIME_SLOTS_START, TIME_SLOTS_END] — используется в экране настройки расписания
    тренера (выбор времён для weekday)."""
    options = []
    current = datetime.combine(date.today(), TIME_SLOTS_START)
    end = datetime.combine(date.today(), TIME_SLOTS_END)
    while current <= end:
        options.append(current.timetz())
        current += timedelta(minutes=TIME_SLOTS_STEP_MINUTES)
    return options


def add_minutes(t: time, minutes: int) -> time:
    """Прибавляет минуты к time-объекту с сохранением tzinfo (используется для
    вычисления end_time слота = start_time + SLOT_DURATION_MINUTES)."""
    dt = datetime.combine(date.today(), t) + timedelta(minutes=minutes)
    return dt.timetz()


# --- Дефолты для настроек тренера (используются при регистрации тренера / если
# у тренера ещё нет собственной записи настроек в БД) ---

DEFAULT_CALENDAR_HORIZON_DAYS = _business.default_calendar_horizon_days  # на сколько дней вперёд календарь виден клиенту при записи
CALENDAR_BUFFER_DAYS = _business.calendar_buffer_days  # на сколько дней вперёд cron держит материализованные слоты (не меньше максимального горизонта 8 нед.)
REMINDER_HOURS_BEFORE_TRAINING = _business.reminder_hours_before_training  # дефолт, если тренер не настроил своё
DEFAULT_MAX_ACTIVE_BOOKINGS = _business.default_max_active_bookings  # сколько активных самостоятельных записей может иметь клиент

# --- Тестовый режим напоминаний ---
# напоминание придёт через REMINDER_TEST_DELAY_MINUTES после подтверждения брони,
# а не за REMINDER_HOURS_BEFORE_TRAINING до тренировки. В проде — False в .env
REMINDER_TEST_MODE = _business.reminder_test_mode
REMINDER_TEST_DELAY_MINUTES = _business.reminder_test_delay_minutes

# --- Дефолты для TrainerPricingRule (если тренер ещё не настроил свои цены) ---

DEFAULT_PRICING_BOUNDARY_TIME = time(0, 0, tzinfo=timezone.utc)  # граница времени "до/после" для разделения цен
DEFAULT_PRICE_BEFORE = Decimal("0")  # цена за тренировку раньше boundary_time (0 = не настроено, цена не показывается)
DEFAULT_PRICE_AFTER = Decimal("0")   # цена за тренировку позже/равно boundary_time


# --- Лейблы для конфигурируемой анкеты клиента (используются как дефолтные
# options при сидинге системных вопросов "здоровье"/"предпочтения" у нового
# тренера — RegisterTrainerUseCase). После сидинга тренер может редактировать
# эти варианты у себя в кабинете независимо от значений ниже. ---

HEALTH_CONDITION_LABELS: dict[HealthCondition, str] = {
    HealthCondition.HEALTHY: "Полностью здоров(-а)",
    HealthCondition.HEART: "Проблемы с сердцем",
    HealthCondition.BACK: "Проблемы со спиной",
    HealthCondition.JOINTS: "Проблемы с суставами",
    HealthCondition.OVERWEIGHT: "Избыточный вес",
    HealthCondition.UNDERWEIGHT: "Недостаточный вес",
    HealthCondition.OTHER: "Другое",
}

GOAL_LABELS: dict[TrainingGoal, str] = {
    TrainingGoal.COMPLEX: "Комплексная (Всё тело + навыки)",
    TrainingGoal.BASIC: "Базовая (Целевые мышцы)",
    TrainingGoal.WEIGHT_LOSS: "Похудение (+консультация)",
    TrainingGoal.WEIGHT_GAIN: "Набор (+консультация)",
    TrainingGoal.CUSTOM_GOAL: "Другое",
}

# Вариант «Другое» в любом MULTI_SELECT-вопросе анкеты: клиент обязан вписать
# свой текст, в ответ сохраняется «Другое: <текст>»
OTHER_OPTION_LABEL = "Другое"
OTHER_OPTION_TEXT_MAX_LENGTH = 200

# --- Заявки клиентов: программа тренировок / консультация / обратная связь ---

PROGRAM_TYPE_LABELS: dict[ProgramType, str] = {
    ProgramType.SINGLE_SESSION: "Разовое занятие",
    ProgramType.WEEK_3: "Неделя (3 занятия)",
    ProgramType.MONTH_2_PER_WEEK: "Месяц (2 раза в неделю)",
    ProgramType.MONTH_3_PER_WEEK: "Месяц (3 раза в неделю)",
}

TRAINING_DIRECTION_LABELS: dict[TrainingDirection, str] = {
    TrainingDirection.STRENGTH: "Силовые тренировки",
    TrainingDirection.CARDIO: "Кардио",
    TrainingDirection.ENDURANCE: "Выносливость",
    TrainingDirection.OFP: "ОФП",
    TrainingDirection.WEIGHT_LOSS: "Снижение веса",
    TrainingDirection.CUSTOM_GOAL: "Конкретная цель",
}

CONSULTATION_TYPE_LABELS: dict[ConsultationType, str] = {
    ConsultationType.FREE: "Бесплатная",
    ConsultationType.PAID: "Платная",
}

CLIENT_REQUEST_KIND_LABELS: dict[ClientRequestKind, str] = {
    ClientRequestKind.PROGRAM: "🏋 Программа тренировок",
    ClientRequestKind.CONSULTATION: "💬 Консультация",
    ClientRequestKind.FEEDBACK: "✉️ Обратная связь",
}

REQUEST_STATUS_LABELS: dict[RequestStatus, str] = {
    RequestStatus.NEW: "🆕 Новая",
    RequestStatus.IN_PROGRESS: "🛠 В работе",
    RequestStatus.DONE: "✅ Закрыта",
    RequestStatus.REJECTED: "🚫 Отклонена",
}

REQUEST_COMMENT_MAX_LENGTH = 255    # comment у program/consultation — VARCHAR(255)
FEEDBACK_MESSAGE_MAX_LENGTH = 1000  # message у feedback_messages — VARCHAR(1000)

# --- Напоминание «запланируйте следующую тренировку» ---
# через сколько дней после завершённой тренировки напомнить клиенту записаться,
# если у него нет будущих записей и он не постоянный клиент
PLAN_NEXT_TRAINING_REMINDER_DAYS = _business.plan_next_training_reminder_days

# --- Подписка тренера ---
# за сколько часов до окончания предупреждать тренера (по убыванию: 48 → 3)
SUBSCRIPTION_WARNING_HOURS: list[int] = sorted(_business.subscription_warning_hours, reverse=True)
# бесплатный пробный период, который новый тренер получает при регистрации (0 — без триала)
TRAINER_TRIAL_DAYS = max(_business.trainer_trial_days, 0)

# --- Тестовый режим постоянных клиентов ---
# cron maintain_recurring_bookings бежит раз в 2 минуты вместо раза в сутки,
# чтобы быстро проверить авто-создание следующей недели. В проде — False в .env
RECURRING_BOOKINGS_TEST_MODE = _business.recurring_bookings_test_mode

# --- Опции для напоминаний (в часах) ---
REMINDER_HOUR_OPTIONS = [1, 2, 3, 4, 6, 12, 24]

# --- Сводка тренеру: «сегодня у вас…» утром и «завтра у вас…» вечером ---
DEFAULT_MORNING_DIGEST_HOUR = _business.morning_digest_hour
MORNING_DIGEST_HOUR_OPTIONS = [6, 7, 8, 9, 10, 11]
EVENING_DIGEST_HOUR_OPTIONS = [18, 19, 20, 21, 22]

# --- «😴 Давно не были»: клиенты без тренировок дольше N дней и без записей ---
INACTIVE_CLIENT_DAYS = _business.inactive_client_days