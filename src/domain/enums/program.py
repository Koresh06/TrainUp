from enum import Enum


class ProgramType(str, Enum):
    SINGLE_SESSION = "single_session"     # разовое занятие
    WEEK_3 = "week_3"                     # неделя, 3 занятия
    MONTH_2_PER_WEEK = "month_2_per_week"  # месяц, 2 раза в неделю
    MONTH_3_PER_WEEK = "month_3_per_week"  # месяц, 3 раза в неделю
