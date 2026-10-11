from aiogram.filters.callback_data import CallbackData

from src.domain.enums.request import ClientRequestKind, RequestStatus


class RequestActionCD(CallbackData, prefix="request"):
    kind: ClientRequestKind
    request_id: int
    status: RequestStatus  # в какой статус перевести заявку
