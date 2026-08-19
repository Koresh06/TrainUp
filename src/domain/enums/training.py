from enum import Enum


class TrainingDirection(str, Enum):
    STRENGTH = "strength"
    CARDIO = "cardio"
    ENDURANCE = "endurance"
    OFP = "ofp"
    WEIGHT_LOSS = "weight_loss"
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