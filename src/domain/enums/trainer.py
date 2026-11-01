from enum import Enum


class TrainerApprovalStatus(str, Enum):
    PENDING = "pending"    # заявка ждёт решения админа
    APPROVED = "approved"
    REJECTED = "rejected"
