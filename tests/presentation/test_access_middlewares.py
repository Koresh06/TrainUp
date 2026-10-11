from types import SimpleNamespace

from aiogram.types import User

from src.application.use_cases.access.get_user_access import UserAccessDTO
from src.presentation.telegram.middlewares.access import (
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
    access = _access(trainer=SimpleNamespace(is_active=True), trainer_subscription_active=True)
    result, called, _ = await _call(TrainerSubscriptionGuard(), {USER_ACCESS_KEY: access})
    assert called and result == "handled"


async def test_trainer_guard_blocks_without_subscription() -> None:
    access = _access(trainer=SimpleNamespace(is_active=True), trainer_subscription_active=False)
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
    admin = User(id=777000, is_bot=False, first_name="A")
    stranger = User(id=1, is_bot=False, first_name="S")
    _, called, _ = await _call(AdminGuard(), {"event_from_user": admin})
    assert called
    _, called, _ = await _call(AdminGuard(), {"event_from_user": stranger})
    assert not called


def test_blocked_flag() -> None:
    assert _access(client=SimpleNamespace(is_active=False)).is_blocked
    assert _access(trainer=SimpleNamespace(is_active=False)).is_blocked
    assert not _access(trainer=SimpleNamespace(is_active=True)).is_blocked
