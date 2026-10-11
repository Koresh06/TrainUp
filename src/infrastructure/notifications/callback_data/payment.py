from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class ManualPaymentAction(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


class ManualPaymentCD(CallbackData, prefix="manual_pay"):
    action: ManualPaymentAction
    external_id: str
