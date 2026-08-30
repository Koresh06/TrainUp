from enum import Enum


class QuestionType(str, Enum):
    MULTI_SELECT = "multi_select"
    TEXT = "text"
