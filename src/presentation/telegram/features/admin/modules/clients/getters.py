from html import escape

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.booking.get_upcoming_by_client import (
    GetUpcomingBookingsByClientRequest,
)
from src.application.use_cases.client.get_by_id import GetClientByIdRequest
from src.application.use_cases.client.search import SearchClientsRequest
from src.application.use_cases.trainer.get_by_id import GetTrainerByIdRequest
from src.domain.entities.booking import Booking
from src.domain.entities.client import Client
from src.domain.entities.trainer import Trainer
from src.utils.timezone import to_moscow


@inject
async def admin_clients_list_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    query: str = dialog_manager.dialog_data.get("clients_query", "")
    clients: list[Client] = await mediator.handle(SearchClientsRequest(query=query))
    return {
        "title": f"🔎 «{escape(query)}»" if query else "🆕 Последние зарегистрированные",
        "clients": [
            {
                "id": str(c.id),
                "label": (
                    f"{'⛔ ' if not c.is_active else ''}"
                    f"{c.first_name} {c.last_name or ''}".strip() + f" · {c.phone}"
                ),
            }
            for c in clients
        ],
        "empty_hint": "" if clients else "\n\nНичего не найдено.",
    }


@inject
async def admin_client_card_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    client: Client = await mediator.handle(
        GetClientByIdRequest(client_id=dialog_manager.dialog_data["client_id"])
    )
    trainer: Trainer = await mediator.handle(GetTrainerByIdRequest(trainer_id=client.trainer_id))
    upcoming: list[Booking] = await mediator.handle(
        GetUpcomingBookingsByClientRequest(client_id=client.id)
    )
    username = f"@{client.username}" if client.username else "—"
    full_name = f"{client.first_name} {client.last_name or ''}".strip()
    text = (
        f"👤 <b>{escape(full_name)}</b>"
        f"{'  ⛔ заблокирован' if not client.is_active else ''}\n"
        f'💬 <a href="tg://user?id={client.tg_id}">написать</a> · {username}\n'
        f"📞 {client.phone} · 🎂 {client.age} лет\n"
        f"🆔 {client.tg_id}\n\n"
        f"👨‍🏫 Тренер: {escape(trainer.name)}\n"
        f"🗓 В боте с {to_moscow(client.created_at).strftime('%d.%m.%Y')}\n"
        f"📅 Предстоящих записей: {len(upcoming)}"
    )
    return {
        "card_text": text,
        "client_name": escape(client.first_name),
        "is_active": client.is_active,
        "is_blocked": not client.is_active,
    }
