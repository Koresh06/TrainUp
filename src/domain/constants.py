from datetime import date, datetime, time, timedelta

SLOT_DURATION_MINUTES = 60

TIME_SLOTS_START = time(8, 0)
TIME_SLOTS_END = time(22, 0)
TIME_SLOTS_STEP_MINUTES = 60

WEEKDAY_LABELS_FULL = [
    "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье",
]


def generate_time_options() -> list[time]:
    options = []
    current = datetime.combine(date.today(), TIME_SLOTS_START)
    end = datetime.combine(date.today(), TIME_SLOTS_END)
    while current <= end:
        options.append(current.timetz())
        current += timedelta(minutes=TIME_SLOTS_STEP_MINUTES)
    return options


def add_minutes(t: time, minutes: int) -> time:
    dt = datetime.combine(date.today(), t) + timedelta(minutes=minutes)
    return dt.timetz() 