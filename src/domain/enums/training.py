from enum import Enum


class TrainingDirection(str, Enum):
    STRENGTH = "strength"
    CARDIO = "cardio"
    ENDURANCE = "endurance"
    OFP = "ofp"
    WEIGHT_LOSS = "weight_loss"
    CUSTOM_GOAL = "custom_goal"