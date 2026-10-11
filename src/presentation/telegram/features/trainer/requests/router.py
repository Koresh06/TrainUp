from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dishka.integrations.aiogram import inject, FromDishka

from src.application.mediator import Mediator
from src.application.use_cases.client_request.update_status import (
    UpdateClientRequestStatusRequest,
)
from src.domain.constants import REQUEST_STATUS_LABELS
from src.domain.enums.request import RequestStatus
from src.infrastructure.notifications.callback_data.request import RequestActionCD

router = Router(name="trainer_requests")


@router.callback_query(RequestActionCD.filter())
@inject
async def on_request_status_click(
    callback: CallbackQuery,
    callback_data: RequestActionCD,
    mediator: FromDishka[Mediator],
) -> None:
    await mediator.handle(
        UpdateClientRequestStatusRequest(
            kind=callback_data.kind,
            request_id=callback_data.request_id,
            status=callback_data.status,
        )
    )
    await callback.answer(REQUEST_STATUS_LABELS[callback_data.status])

    # после «В работу» оставляем только «Закрыть», после закрытия — без кнопок
    reply_markup = None
    if callback_data.status == RequestStatus.IN_PROGRESS:
        kb = InlineKeyboardBuilder()
        kb.button(
            text="✅ Закрыть",
            callback_data=RequestActionCD(
                kind=callback_data.kind,
                request_id=callback_data.request_id,
                status=RequestStatus.DONE,
            ).pack(),
        )
        reply_markup = kb.as_markup()

    await callback.message.edit_text(
        f"{callback.message.html_text}\n\n📌 {REQUEST_STATUS_LABELS[callback_data.status]}",
        reply_markup=reply_markup,
    )
