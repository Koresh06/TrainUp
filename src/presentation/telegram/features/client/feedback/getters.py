from html import escape

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.client.get_by_tg_id import GetClientByTgIdRequest
from src.application.use_cases.faq.get_active import GetActiveFaqItemsRequest
from src.application.use_cases.faq.get_by_id import GetFaqItemByIdRequest
from src.domain.entities.client import Client
from src.domain.entities.faq import FaqItem


@inject
async def callback_confirm_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    client: Client = await mediator.handle(
        GetClientByTgIdRequest(tg_id=dialog_manager.event.from_user.id)
    )
    # карточку мог завести тренер без телефона — тогда сразу просим номер
    return {"phone": client.phone or "—", "has_phone": client.phone is not None}


@inject
async def faq_list_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    items: list[FaqItem] = await mediator.handle(GetActiveFaqItemsRequest())
    return {
        "faq_items": [{"id": str(item.id), "label": item.question} for item in items],
        "empty_hint": "" if items else "\n\nПока здесь пусто.",
    }


@inject
async def faq_answer_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    item: FaqItem = await mediator.handle(
        GetFaqItemByIdRequest(faq_id=dialog_manager.dialog_data["faq_id"])
    )
    return {"question": escape(item.question), "answer": escape(item.answer)}
