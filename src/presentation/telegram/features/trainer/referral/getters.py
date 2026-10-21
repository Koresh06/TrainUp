from html import escape
from urllib.parse import quote

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.trainer.referral import (
    TRAINER_REFERRAL_PREFIX,
    GetTrainerReferralInfoRequest,
    TrainerReferralInfoDTO,
)
from src.core.config import settings
from src.domain.constants import TRAINER_TRIAL_DAYS
from src.presentation.telegram.features.trainer.register.texts import days_word


@inject
async def trainer_referral_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    info: TrainerReferralInfoDTO = await mediator.handle(
        GetTrainerReferralInfoRequest(trainer_id=dialog_manager.start_data["trainer_id"])
    )
    link = f"https://t.me/{settings.telegram.bot_username}?start={TRAINER_REFERRAL_PREFIX}{info.code}"

    friend_trial = TRAINER_TRIAL_DAYS + info.friend_days
    steps = ["1️⃣ Отправьте коллеге-тренеру ссылку ниже."]
    if info.friend_days:
        steps.append(
            f"2️⃣ Он регистрируется в TrainUp и получает пробный период на "
            f"<b>{info.friend_days} {days_word(info.friend_days)} длиннее</b> — "
            f"{friend_trial} {days_word(friend_trial)} вместо {TRAINER_TRIAL_DAYS}."
        )
    else:
        steps.append("2️⃣ Он регистрируется в TrainUp и пользуется пробным периодом.")
    if info.bonus_days:
        steps.append(
            f"3️⃣ Когда он оформит первую <b>платную</b> подписку — вам "
            f"<b>+{info.bonus_days} {days_word(info.bonus_days)}</b> подписки бесплатно. "
            f"Дни добавятся к вашей текущей подписке."
        )
    rules = (
        "Бонус — за каждого коллегу, количество приглашений не ограничено. "
        "Пробный период сам по себе бонус не даёт — только оплата."
        if info.bonus_days
        else ""
    )

    if info.invited:
        lines = [
            f"• {escape(t.name)} — "
            + ("✅ оформил подписку, бонус начислен" if t.referral_rewarded_at else "⏳ пробный период")
            for t in info.invited
        ]
        invited = f"👥 <b>Приглашено: {len(info.invited)}</b>\n" + "\n".join(lines)
    else:
        invited = "👥 Пока никого — станьте первым 🙂"

    return {
        "steps": "\n".join(steps),
        "rules": f"\n\n<i>{rules}</i>" if rules else "",
        "link": link,
        "invited": invited,
        "share_url": (
            f"https://t.me/share/url?url={quote(link)}"
            f"&text={quote('Веду клиентов и расписание в TrainUp — попробуй, по ссылке пробный период длиннее')}"
        ),
    }
