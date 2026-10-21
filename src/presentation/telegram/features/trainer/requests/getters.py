from html import escape

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.client.get_by_id import GetClientByIdRequest
from src.application.use_cases.client_request._shared import ClientRequestDTO
from src.application.use_cases.client_request.get_by_id import (
    GetClientRequestByIdRequest,
)
from src.application.use_cases.client_request.get_by_trainer import (
    GetClientRequestsByTrainerRequest,
)
from src.domain.constants import CLIENT_REQUEST_KIND_LABELS, REQUEST_STATUS_LABELS
from src.domain.entities.client import Client
from src.domain.enums.request import RequestStatus
from src.utils.timezone import to_moscow

from .constants import (
    REQUEST_KIND_ICONS,
    REQUESTS_FILTER_LABELS,
    REQUESTS_FILTER_STATUSES,
    RequestsFilter,
    pack_request_item_id,
    unpack_request_item_id,
)


def current_filter(dialog_manager: DialogManager) -> RequestsFilter:
    return RequestsFilter(
        dialog_manager.dialog_data.get("requests_filter", RequestsFilter.NEW.value)
    )


@inject
async def requests_list_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    trainer_id: int = dialog_manager.start_data["trainer_id"]
    active_filter = current_filter(dialog_manager)

    requests: list[ClientRequestDTO] = await mediator.handle(
        GetClientRequestsByTrainerRequest(
            trainer_id=trainer_id,
            statuses=REQUESTS_FILTER_STATUSES[active_filter],
        )
    )

    items = []
    for request in requests:
        client: Client = await mediator.handle(
            GetClientByIdRequest(client_id=request.client_id)
        )
        client_short = client.first_name
        if client.last_name:
            client_short += f" {client.last_name[0]}."
        items.append(
            {
                "id": pack_request_item_id(request.kind, request.id),
                "label": (
                    f"{REQUEST_KIND_ICONS[request.kind]} "
                    f"{to_moscow(request.created_at).strftime('%d.%m %H:%M')} — "
                    f"{client_short}"
                ),
            }
        )

    return {
        "requests": items,
        "empty_hint": "" if items else "\n\nЗаявок нет",
        **{
            f"lbl_{f.value}": ("🟢 " if f == active_filter else "") + label
            for f, label in REQUESTS_FILTER_LABELS.items()
        },
    }


@inject
async def request_detail_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    kind, request_id = unpack_request_item_id(dialog_manager.dialog_data["request_item_id"])
    request: ClientRequestDTO = await mediator.handle(
        GetClientRequestByIdRequest(kind=kind, request_id=request_id)
    )
    client: Client = await mediator.handle(GetClientByIdRequest(client_id=request.client_id))

    contact_lines = [
        f'💬 <a href="tg://user?id={client.tg_id}">Написать клиенту в Telegram</a>'
    ]
    if client.username:
        contact_lines.append(f"👤 @{client.username}")
    contact_lines.append(f"📞 {client.phone or '—'}")

    return {
        "kind_label": CLIENT_REQUEST_KIND_LABELS[request.kind],
        "title": escape(request.title),
        "details": escape(request.details),
        "client_name": escape(f"{client.first_name} {client.last_name or ''}".strip()),
        "contact_block": "\n".join(contact_lines),
        "created_at": to_moscow(request.created_at).strftime("%d.%m.%Y %H:%M"),
        "status": REQUEST_STATUS_LABELS[request.status],
        "can_take": request.status == RequestStatus.NEW,
        "can_close": request.status in (RequestStatus.NEW, RequestStatus.IN_PROGRESS),
        "can_reopen": request.status in (RequestStatus.DONE, RequestStatus.REJECTED),
    }
