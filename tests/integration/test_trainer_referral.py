"""Реферальная программа тренеров: длинный пробный период приглашённому,
бонусные дни пригласившему после первой оплаты — один раз."""

from src.application.use_cases.subscription.get_active import GetActiveSubscriptionRequest
from src.application.use_cases.subscription.get_by_trainer import GetSubscriptionsByTrainerRequest
from src.application.use_cases.subscription.grant import GrantSubscriptionRequest
from src.application.use_cases.trainer.referral import (
    GetTrainerReferralInfoRequest,
    ResolveTrainerReferralCodeRequest,
)
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.domain.constants import TRAINER_REFERRAL_BONUS_DAYS, TRAINER_REFERRAL_FRIEND_DAYS
from src.domain.enums.subscription import SubscriptionSource


async def test_trainer_referral_flow(run, notifications) -> None:
    alice = await run(RegisterTrainerRequest(tg_id=1001, name="Алиса", bio="", notification_chat_id=-1))
    info = await run(GetTrainerReferralInfoRequest(trainer_id=alice.id))
    assert info.code and info.invited == []
    assert (await run(ResolveTrainerReferralCodeRequest(code=info.code))).id == alice.id
    assert await run(ResolveTrainerReferralCodeRequest(code="nope")) is None

    bob = await run(
        RegisterTrainerRequest(
            tg_id=1002, name="Боб", bio="", notification_chat_id=-2, referred_by_trainer_id=alice.id
        )
    )
    assert bob.referred_by_trainer_id == alice.id
    # в тестах обычного триала нет (TRAINER_TRIAL_DAYS=0) — только бонус по приглашению
    trial = await run(GetActiveSubscriptionRequest(trainer_id=bob.id))
    assert trial.source == SubscriptionSource.TRIAL
    assert (trial.expired_at - trial.started_at).days == TRAINER_REFERRAL_FRIEND_DAYS
    assert any("зарегистрировался по вашей ссылке" in t for c, t in notifications.of("send") if c == alice.tg_id)

    # бесплатный период от админа — не оплата, бонуса нет
    await run(GrantSubscriptionRequest(trainer_id=bob.id, source=SubscriptionSource.TRIAL, days=3))
    assert await run(GetActiveSubscriptionRequest(trainer_id=alice.id)) is None

    # первая оплата (наличными через админа) — пригласившему бонус, второй раз — нет
    for _ in range(2):
        await run(GrantSubscriptionRequest(trainer_id=bob.id, source=SubscriptionSource.CASH, days=30))
    alice_subs = await run(GetSubscriptionsByTrainerRequest(trainer_id=alice.id))
    assert [s.source for s in alice_subs] == [SubscriptionSource.REFERRAL]
    [bonus] = alice_subs
    assert (bonus.expired_at - bonus.started_at).days == TRAINER_REFERRAL_BONUS_DAYS
    assert any("вам начислено" in t for c, t in notifications.of("send") if c == alice.tg_id)

    info = await run(GetTrainerReferralInfoRequest(trainer_id=alice.id))
    assert [t.id for t in info.invited] == [bob.id] and info.rewarded == 1
