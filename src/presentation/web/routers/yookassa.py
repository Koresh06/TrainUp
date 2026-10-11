import logging

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException, Request

from src.application.interfaces.task_queue import TaskQueue
from src.application.services.payment_provider_registry import PaymentProviderRegistry
from src.domain.enums.payment import PaymentMethod
from src.domain.exception.payment import PaymentProviderNotFoundException
from src.infrastructure.payment.providers.yookassa import YooKassaProvider

logger = logging.getLogger(__name__)

router = APIRouter()


async def process_yookassa_webhook(
    payload: dict,
    *,
    task_queue: TaskQueue,
    provider_registry: PaymentProviderRegistry,
) -> dict:
    """Логика webhook'а отдельно от FastAPI-роута — чтобы тестировать без HTTP.
    Событию из тела НЕ доверяем: статус перепроверяется запросом в API ЮKassa."""
    yookassa_payment_id = (payload.get("object") or {}).get("id")
    logger.info(
        "[YooKassa:webhook] event=%s payment_id=%s",
        payload.get("event"),
        yookassa_payment_id,
    )
    if not yookassa_payment_id:
        raise HTTPException(status_code=400, detail="Invalid payload")

    try:
        provider = provider_registry.get(PaymentMethod.YOOKASSA)
    except PaymentProviderNotFoundException:
        # чаще всего — процесс webhook запущен до включения ЮKassa в .env
        logger.error(
            "[YooKassa:webhook] provider disabled in this process — check "
            "APP_CONFIG__PAYMENT__YOOKASSA__ENABLED and restart the webhook service"
        )
        raise HTTPException(status_code=404, detail="YooKassa is disabled")
    if not isinstance(provider, YooKassaProvider):
        raise HTTPException(status_code=500, detail="Provider misconfigured")

    verified = await provider.verify_payment(yookassa_payment_id)
    if verified is None:
        # временная ошибка API — пусть ЮKassa пришлёт webhook повторно
        raise HTTPException(status_code=502, detail="Could not verify payment")

    external_id = (verified.metadata or {}).get("external_id")
    if not external_id:
        raise HTTPException(status_code=400, detail="Invalid metadata")

    if verified.status == "succeeded" and verified.paid:
        await task_queue.enqueue(task_name="confirm_payment", args=(external_id,))
    elif verified.status == "canceled":
        await task_queue.enqueue(task_name="reject_payment", args=(external_id,))
    else:
        logger.info(
            "[YooKassa:webhook:ignored] external_id=%s status=%s",
            external_id,
            verified.status,
        )
    return {"status": "ok"}


@router.post("/webhook/yookassa")
@inject
async def yookassa_webhook(
    request: Request,
    task_queue: FromDishka[TaskQueue],
    provider_registry: FromDishka[PaymentProviderRegistry],
) -> dict:
    return await process_yookassa_webhook(
        await request.json(),
        task_queue=task_queue,
        provider_registry=provider_registry,
    )
