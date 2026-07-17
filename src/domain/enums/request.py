from enum import Enum


class RequestStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    REJECTED = "rejected"
