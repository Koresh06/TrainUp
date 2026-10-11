from enum import Enum

from src.domain.enums.request import ClientRequestKind, RequestStatus


class RequestsFilter(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


REQUESTS_FILTER_STATUSES: dict[RequestsFilter, tuple[RequestStatus, ...]] = {
    RequestsFilter.NEW: (RequestStatus.NEW,),
    RequestsFilter.IN_PROGRESS: (RequestStatus.IN_PROGRESS,),
    RequestsFilter.CLOSED: (RequestStatus.DONE, RequestStatus.REJECTED),
}

REQUESTS_FILTER_LABELS: dict[RequestsFilter, str] = {
    RequestsFilter.NEW: "🆕 Новые",
    RequestsFilter.IN_PROGRESS: "🛠 В работе",
    RequestsFilter.CLOSED: "✅ Закрытые",
}

REQUEST_KIND_ICONS: dict[ClientRequestKind, str] = {
    ClientRequestKind.PROGRAM: "🏋",
    ClientRequestKind.CONSULTATION: "💬",
    ClientRequestKind.FEEDBACK: "✉️",
}


def pack_request_item_id(kind: ClientRequestKind, request_id: int) -> str:
    return f"{kind.value}:{request_id}"


def unpack_request_item_id(item_id: str) -> tuple[ClientRequestKind, int]:
    kind, request_id = item_id.split(":", 1)
    return ClientRequestKind(kind), int(request_id)
