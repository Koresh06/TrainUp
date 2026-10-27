from html import escape

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.faq.get_active import GetActiveFaqItemsRequest
from src.application.use_cases.faq.get_by_id import GetFaqItemByIdRequest
from src.domain.entities.faq import FaqItem
from src.domain.enums.faq import FaqAudience

FAQ_AUDIENCE_LABELS: dict[FaqAudience, str] = {
    FaqAudience.CLIENT: "👥 FAQ клиентов",
    FaqAudience.TRAINER: "👨‍🏫 FAQ тренеров",
}
FAQ_AUDIENCE_HINTS: dict[FaqAudience, str] = {
    FaqAudience.CLIENT: "Клиенты видят его в «✉️ Обратная связь → ❓ Частые вопросы».",
    FaqAudience.TRAINER: "Тренеры видят его в кабинете: «❓ Помощь» — правила пользования ботом.",
}


def current_audience(dialog_manager: DialogManager) -> FaqAudience:
    return FaqAudience(
        dialog_manager.dialog_data.get(
            "faq_audience",
            FaqAudience.CLIENT.value,
        )
    )


@inject
async def admin_faq_list_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    audience = current_audience(dialog_manager)
    items: list[FaqItem] = await mediator.handle(
        GetActiveFaqItemsRequest(audience=audience)
    )
    return {
        "audience_label": FAQ_AUDIENCE_LABELS[audience],
        "audience_hint": FAQ_AUDIENCE_HINTS[audience],
        "faq_items": [{"id": str(item.id), "label": item.question} for item in items],
        "empty_hint": "" if items else "\n\nСписок пуст.",
    }


@inject
async def admin_faq_detail_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    item: FaqItem = await mediator.handle(
        GetFaqItemByIdRequest(faq_id=dialog_manager.dialog_data["faq_id"])
    )
    return {"question": escape(item.question), "answer": escape(item.answer)}


async def admin_faq_new_question_getter(
    dialog_manager: DialogManager, **kwargs
) -> dict:
    return {"new_question": escape(dialog_manager.dialog_data.get("new_question", ""))}
