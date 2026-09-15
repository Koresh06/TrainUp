from enum import Enum


class TrainingDirection(str, Enum):
    STRENGTH = "strength"
    CARDIO = "cardio"
    ENDURANCE = "endurance"
    OFP = "ofp"
    WEIGHT_LOSS = "weight_loss"
    CUSTOM_GOAL = "custom_goal"


class TrainingGoal(str, Enum):
    COMPLEX = "complex"
    BASIC = "basic"
    WEIGHT_LOSS = "weight_loss"
    WEIGHT_GAIN = "weight_gain"
    CUSTOM_GOAL = "custom_goal"


class SportExperience(str, Enum):
    NONE = "none"
    UP_TO_3_MONTHS = "up_to_3_months"
    UP_TO_6_MONTHS = "up_to_6_months"
    MORE_THAN_YEAR = "more_than_year"


class HealthCondition(str, Enum):
    HEALTHY = "healthy"
    HEART = "heart"
    BACK = "back"
    JOINTS = "joints"
    OVERWEIGHT = "overweight"
    UNDERWEIGHT = "underweight"
    OTHER = "other"


SPORT_EXPERIENCE_LABELS: dict[SportExperience, str] = {
    SportExperience.NONE: "Нет опыта",
    SportExperience.UP_TO_3_MONTHS: "До 3 месяцев",
    SportExperience.UP_TO_6_MONTHS: "До 6 месяцев",
    SportExperience.MORE_THAN_YEAR: "Более 1 года",
}