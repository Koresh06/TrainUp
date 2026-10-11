from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.application.mediator import Mediator
from src.application.use_cases.payment.get_by_external_id import (
    GetPaymentByExternalIdRequest,
)
from src.core.config import settings
from src.domain.enums.payment import PaymentStatus
from src.domain.exception.payment import PaymentNotFoundException

router = APIRouter()

_PAGES = {
    PaymentStatus.PAID: ("✅ Оплата прошла", "Подписка активна — вернитесь в бота."),
    PaymentStatus.PENDING: (
        "⏳ Платёж обрабатывается",
        "Как только банк подтвердит оплату, бот пришлёт сообщение.",
    ),
    PaymentStatus.FAILED: ("❌ Оплата не прошла", "Попробуйте ещё раз из бота."),
}


def _page(title: str, text: str) -> HTMLResponse:
    bot_url = f"https://t.me/{settings.telegram.bot_username}"
    return HTMLResponse(
        f"""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:480px;margin:15vh auto;
padding:0 16px;text-align:center}}a{{display:inline-block;margin-top:24px;
padding:12px 24px;border-radius:12px;background:#2AABEE;color:#fff;
text-decoration:none}}</style></head><body><h1>{title}</h1><p>{text}</p>
<a href="{bot_url}">Вернуться в бота</a></body></html>"""
    )


@router.get("/payment/return", response_class=HTMLResponse)
@inject
async def payment_return(
    mediator: FromDishka[Mediator],
    external_id: str | None = None,
) -> HTMLResponse:
    if not external_id:
        return _page(*_PAGES[PaymentStatus.FAILED])
    try:
        payment = await mediator.handle(GetPaymentByExternalIdRequest(external_id=external_id))
    except PaymentNotFoundException:
        return _page(*_PAGES[PaymentStatus.FAILED])
    return _page(*_PAGES.get(payment.status, _PAGES[PaymentStatus.PENDING]))
