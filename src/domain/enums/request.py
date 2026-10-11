from enum import Enum


class RequestStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    REJECTED = "rejected"


class ClientRequestKind(str, Enum):
    PROGRAM = "program"            # заявка на программу тренировок
    CONSULTATION = "consultation"  # заявка на консультацию
    FEEDBACK = "feedback"          # обратная связь: звонок / сообщение тренеру
