from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class TrainerApprovalAction(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


class TrainerApprovalCD(CallbackData, prefix="trainer_approval"):
    action: TrainerApprovalAction
    trainer_id: int
