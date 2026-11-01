from types import SimpleNamespace

from src.application.use_cases.access.get_user_access import UserAccessDTO
from src.domain.entities.bot_admin import AdminAccess
from src.domain.enums.admin import AdminPermission
from src.domain.enums.trainer import TrainerApprovalStatus
from src.presentation.telegram.middlewares.access import (
    ADMIN_ACCESS_KEY,
    USER_ACCESS_KEY,
    AdminGuard,
    ClientTrainerGuard,
    TrainerSubscriptionGuard,
)


class FakeMessage:
    def __init__(self) -> None:
        self.answers: list[tuple[str, object]] = []

    async def answer(self, text: str, reply_markup=None) -> None:
        self.answers.append((text, reply_markup))


async def _call(middleware, data: dict, event=None):
    called = []

    async def handler(event, data):
        called.append(True)
        return "handled"

    event = event or FakeMessage()
    result = await middleware(handler, event, data)
    return result, bool(called), event


def _access(**kwargs) -> UserAccessDTO:
    defaults = dict(trainer=None, trainer_subscription_active=False, client=None, client_trainer_available=False)
    defaults.update(kwargs)
    return UserAccessDTO(**defaults)


async def test_trainer_guard_passes_with_subscription() -> None:
    access = _access(trainer=SimpleNamespace(is_active=True, is_approved=True), trainer_subscription_active=True)
    result, called, _ = await _call(TrainerSubscriptionGuard(), {USER_ACCESS_KEY: access})
    assert called and result == "handled"


async def test_trainer_guard_blocks_without_subscription() -> None:
    access = _access(trainer=SimpleNamespace(is_active=True, is_approved=True), trainer_subscription_active=False)
    _, called, _ = await _call(TrainerSubscriptionGuard(), {USER_ACCESS_KEY: access})
    assert not called


async def test_trainer_guard_blocks_pending_even_with_subscription() -> None:
    # админ мог выдать подписку ещё не подтверждённому тренеру
    trainer = SimpleNamespace(
        is_active=True, is_approved=False, approval_status=TrainerApprovalStatus.PENDING
    )
    access = _access(trainer=trainer, trainer_subscription_active=True)
    _, called, _ = await _call(TrainerSubscriptionGuard(), {USER_ACCESS_KEY: access})
    assert not called


async def test_client_guard() -> None:
    client = SimpleNamespace(is_active=True)
    _, called, _ = await _call(ClientTrainerGuard(), {USER_ACCESS_KEY: _access(client=client, client_trainer_available=True)})
    assert called
    _, called, _ = await _call(ClientTrainerGuard(), {USER_ACCESS_KEY: _access(client=client)})
    assert not called


async def test_guards_skip_when_no_access_info() -> None:
    # групповые чаты (кнопки в рабочей группе тренера) — без проверки
    for guard in (TrainerSubscriptionGuard(), ClientTrainerGuard()):
        _, called, _ = await _call(guard, {})
        assert called


async def test_admin_guard() -> None:
    admin = AdminAccess(tg_id=1, is_super=False, permissions=frozenset({AdminPermission.FAQ}))
    boss = AdminAccess(tg_id=2, is_super=True)

    for guard, access, allowed in (
        (AdminGuard(), admin, True),
        (AdminGuard(), None, False),
        (AdminGuard(AdminPermission.FAQ), admin, True),
        (AdminGuard(AdminPermission.STATS), admin, False),
        (AdminGuard(AdminPermission.STATS), boss, True),
        (AdminGuard(super_only=True), admin, False),
        (AdminGuard(super_only=True), boss, True),
    ):
        _, called, _ = await _call(guard, {ADMIN_ACCESS_KEY: access})
        assert called is allowed


def test_blocked_flag() -> None:
    assert _access(client=SimpleNamespace(is_active=False)).is_blocked
    assert _access(trainer=SimpleNamespace(is_active=False)).is_blocked
    assert not _access(trainer=SimpleNamespace(is_active=True)).is_blocked
