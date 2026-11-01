import pytest

from src.application.use_cases.access.get_user_access import GetUserAccessRequest
from src.application.use_cases.access.is_trainer_available import IsTrainerAvailableRequest
from src.application.use_cases.subscription.get_active import GetActiveSubscriptionRequest
from src.application.use_cases.trainer.get_applications import (
    GetTrainerApplicationsRequest,
)
from src.application.use_cases.trainer.register import RegisterTrainerRequest
from src.application.use_cases.trainer.review import ReviewTrainerRequest
from src.core.dependencies.providers import use_cases as providers
from src.domain.enums.trainer import TrainerApprovalStatus
from src.domain.exception.trainer import TrainerAlreadyReviewedException
from tests.factories import make_trainer

ADMIN = 777000


@pytest.fixture(autouse=True)
def approval_on(monkeypatch):
    monkeypatch.setattr(providers, "TRAINER_APPROVAL_REQUIRED", True)
    monkeypatch.setattr(providers, "TRAINER_TRIAL_DAYS", 7)


async def _register(run, **kwargs):
    return await run(
        RegisterTrainerRequest(
            tg_id=1001, name="Иван", bio="Тренер", notification_chat_id=-1,
            phone="+375291112233", username="ivan", group_title="Зал", **kwargs,
        )
    )


def _review(trainer, approve=True, **kwargs) -> ReviewTrainerRequest:
    return ReviewTrainerRequest(
        trainer_id=trainer.id, approve=approve, reviewed_by_tg_id=ADMIN, **kwargs
    )


async def test_new_trainer_waits_and_admin_gets_full_card(run, notifications) -> None:
    trainer = await _register(run)

    assert trainer.approval_status == TrainerApprovalStatus.PENDING
    assert await run(GetActiveSubscriptionRequest(trainer_id=trainer.id)) is None
    assert not await run(IsTrainerAvailableRequest(trainer_id=trainer.id))
    [card] = notifications.of("notify_trainer_application")
    for expected in ("Иван", "@ivan", "+375291112233", "Тренер", "Зал", "1001"):
        assert expected in card
    assert notifications.application_recipients == [ADMIN]
    assert [t.id for t in await run(GetTrainerApplicationsRequest())] == [trainer.id]


async def test_approval_starts_trial_and_opens_access(run, notifications) -> None:
    trainer = await _register(run)
    approved = await run(_review(trainer))

    assert approved.is_approved
    assert await run(GetActiveSubscriptionRequest(trainer_id=trainer.id)) is not None
    assert await run(IsTrainerAvailableRequest(trainer_id=trainer.id))
    assert (await run(GetUserAccessRequest(tg_id=1001))).trainer_subscription_active
    assert any("одобрена" in call for call in map(str, notifications.calls))
    assert await run(GetTrainerApplicationsRequest()) == []


async def test_repeated_approval_does_not_grant_second_trial(run) -> None:
    trainer = await _register(run)
    await run(_review(trainer))
    with pytest.raises(TrainerAlreadyReviewedException):
        await run(_review(trainer))


async def test_approved_trainer_cannot_be_rejected_by_stale_button(run) -> None:
    trainer = await _register(run)
    await run(_review(trainer))
    with pytest.raises(TrainerAlreadyReviewedException):
        await run(_review(trainer, approve=False, only_pending=True))


async def test_rejected_gets_nothing_but_can_be_approved_later(run) -> None:
    trainer = await _register(run)
    rejected = await run(_review(trainer, approve=False))
    assert rejected.approval_status == TrainerApprovalStatus.REJECTED
    assert await run(GetActiveSubscriptionRequest(trainer_id=trainer.id)) is None

    # старая кнопка в уведомлении не перебьёт решение другого админа
    with pytest.raises(TrainerAlreadyReviewedException):
        await run(_review(trainer, only_pending=True))
    assert (await run(_review(trainer))).is_approved


async def test_referrer_hears_only_after_approval(run, session, notifications) -> None:
    referrer = await make_trainer(session, tg_id=2002)
    trainer = await _register(run, referred_by_trainer_id=referrer.id)
    assert not any(c for c in map(str, notifications.calls) if "по вашей ссылке" in c)

    await run(_review(trainer))
    assert any(c for c in map(str, notifications.calls) if "по вашей ссылке" in c)
