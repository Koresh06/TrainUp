from decimal import Decimal
from html import escape

from src.application.interfaces.notification_service import NotificationService
from src.application.use_cases.subscription._shared import _activate_subscription
from src.domain.constants import TRAINER_REFERRAL_BONUS_DAYS
from src.domain.entities.trainer import Trainer
from src.domain.enums.subscription import SubscriptionPlan, SubscriptionSource
from src.domain.repositories.subscription import TrainerSubscriptionRepository
from src.utils.timezone import to_moscow


async def start_trial(
    trainer: Trainer,
    has_referrer: bool,
    subscription_repo: TrainerSubscriptionRepository,
    trial_days: int,
    referral_friend_days: int,
) -> int:
    """Пробный период нового тренера: по приглашению другого тренера он длиннее.
    Регистрация одна на tg_id, так что повторно триал не получить."""
    days = trial_days + (referral_friend_days if has_referrer else 0)
    if days > 0:
        await _activate_subscription(
            subscription_repo=subscription_repo,
            trainer_id=trainer.id,
            plan=SubscriptionPlan.CUSTOM,
            amount=Decimal("0"),
            source=SubscriptionSource.TRIAL,
            days=days,
        )
    return days


async def notify_referrer(
    trainer: Trainer, referrer: Trainer, notification_service: NotificationService
) -> None:
    bonus = (
        f" Когда он оформит подписку, вам начислится "
        f"<b>+{TRAINER_REFERRAL_BONUS_DAYS} дней</b> бесплатно."
        if TRAINER_REFERRAL_BONUS_DAYS
        else ""
    )
    await notification_service.send(
        chat_id=referrer.tg_id,
        text=(
            f"🎉 Тренер <b>{escape(trainer.name)}</b> зарегистрировался "
            f"по вашей ссылке.{bonus}"
        ),
    )


def trainer_application_text(
    trainer: Trainer,
    referrer: Trainer | None,
    username: str | None = None,
    group_title: str | None = None,
) -> str:
    """Всё, что есть о кандидате, — и в уведомлении, и в карточке админки."""
    lines = [
        "🛂 <b>Заявка тренера</b>\n",
        f"👤 {escape(trainer.name)}",
        f'💬 <a href="tg://user?id={trainer.tg_id}">написать</a>'
        + (f" · @{escape(username)}" if username else ""),
        f"🆔 <code>{trainer.tg_id}</code>",
        f"📞 {escape(trainer.phone or '—')}",
        f"📝 {escape(trainer.bio or '—')}",
    ]
    if group_title:
        lines.append(f"🔔 Рабочая группа: {escape(group_title)}")
    if referrer is not None:
        lines.append(f"🤝 Пригласил: {escape(referrer.name)}")
    lines.append(f"🗓 Заявка от {to_moscow(trainer.created_at).strftime('%d.%m.%Y %H:%M')}")
    return "\n".join(lines)
