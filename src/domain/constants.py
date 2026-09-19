from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from src.domain.enums.training import HealthCondition, TrainingGoal

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

DEFAULT_CALENDAR_HORIZON_DAYS = 14  # на сколько дней вперёд генерируется календарь и виден клиенту при записи
REMINDER_HOURS_BEFORE_TRAINING = 2  # за сколько часов до тренировки отправляется напоминание клиенту (боевое значение)
DEFAULT_MAX_ACTIVE_BOOKINGS = 1     # сколько активных записей одновременно может иметь один клиент у тренера (пока не подключено к реальной проверке)

# --- Тестовый режим напоминаний ---
# ВРЕМЕННО для теста — напоминание придёт через REMINDER_TEST_DELAY_MINUTES после
# подтверждения брони, а не за REMINDER_HOURS_BEFORE_TRAINING до тренировки.
# Перед деплоем в прод — выставить обратно в False!
REMINDER_TEST_MODE = False
REMINDER_TEST_DELAY_MINUTES = 1

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
    TrainingGoal.CUSTOM_GOAL: "Другое (указать самостоятельно)",
}

# --- Тестовый режим постоянных клиентов ---
# ВРЕМЕННО для теста — cron maintain_recurring_bookings бежит раз в 2 минуты
# вместо раз в сутки, чтобы быстро проверить авто-создание следующей недели.
# Перед деплоем в прод — выставить обратно в False!
RECURRING_BOOKINGS_TEST_MODE = False

# --- Опции для напоминаний (в часах) ---
REMINDER_HOUR_OPTIONS = [1, 2, 3, 4, 6, 12, 24]