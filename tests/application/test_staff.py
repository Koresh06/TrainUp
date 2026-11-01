import pytest

from src.application.interfaces.notification_service import ManualPaymentRequestDTO
from src.application.use_cases.staff.get_access import (
    GetAdminAccessRequest,
    GetAdminAccessUseCase,
)
from src.domain.entities.bot_admin import AdminAccess, BotAdmin
from src.domain.enums.admin import AdminNotification, AdminPermission
from tests.fakes.common import FakeBotAdmins, RecordingNotifications, make_admin_notifier

BOSS = 777000
HELPER = 42

MANUAL = ManualPaymentRequestDTO(
    external_id="e",
    trainer_name="T",
    trainer_tg_id=1,
    trainer_phone=None,
    plan_label="p",
    amount_label="$1",
)


def helper(*permissions, muted=()) -> BotAdmin:
    return BotAdmin(tg_id=HELPER, permissions=set(permissions), muted_notifications=set(muted))


def test_manage_permission_implies_view() -> None:
    access = AdminAccess(
        tg_id=1,
        is_super=False,
        permissions=frozenset({AdminPermission.TRAINERS_MANAGE}),
    )
    assert access.can(AdminPermission.TRAINERS_VIEW)
    assert not access.can(AdminPermission.CLIENTS_VIEW)

    viewer = AdminAccess(
        tg_id=1,
        is_super=False,
        permissions=frozenset({AdminPermission.TRAINERS_VIEW}),
    )
    assert not viewer.can(AdminPermission.TRAINERS_MANAGE)


async def test_access_super_from_settings_regular_from_db() -> None:
    use_case = GetAdminAccessUseCase(
        admin_repo=FakeBotAdmins([helper(AdminPermission.FAQ)]), super_admin_ids=[BOSS]
    )
    assert (await use_case(GetAdminAccessRequest(tg_id=BOSS))).is_super
    regular = await use_case(GetAdminAccessRequest(tg_id=HELPER))
    assert not regular.is_super and regular.permissions == {AdminPermission.FAQ}
    assert await use_case(GetAdminAccessRequest(tg_id=1)) is None


@pytest.mark.parametrize(
    "admins, expected",
    [
        pytest.param([], [BOSS], id="only_super"),
        pytest.param([helper(AdminPermission.PAYMENTS)], [BOSS, HELPER], id="with_permission"),
        pytest.param([helper(AdminPermission.FAQ)], [BOSS], id="without_permission"),
        pytest.param(
            [helper(AdminPermission.PAYMENTS, muted=[AdminNotification.PAYMENT_PAID])],
            [BOSS],
            id="muted",
        ),
        pytest.param(
            [BotAdmin(tg_id=BOSS, muted_notifications={AdminNotification.PAYMENT_PAID})],
            [],
            id="super_muted",
        ),
    ],
)
async def test_recipients(admins, expected) -> None:
    notifications = RecordingNotifications()
    await make_admin_notifier(notifications, admins).notify(
        AdminNotification.PAYMENT_PAID, "paid"
    )
    if expected:
        assert notifications.admin_recipients == expected
    else:
        assert notifications.of("notify_admins") == []


async def test_manual_payment_goes_to_helper_when_super_muted() -> None:
    notifications = RecordingNotifications()
    boss = BotAdmin(tg_id=BOSS, muted_notifications={AdminNotification.MANUAL_PAYMENT})
    await make_admin_notifier(
        notifications, [boss, helper(AdminPermission.PAYMENTS)]
    ).notify_manual_payment(MANUAL)
    assert notifications.manual_payment_recipients == [HELPER]


async def test_manual_payment_never_lost_when_everyone_muted() -> None:
    notifications = RecordingNotifications()
    boss = BotAdmin(tg_id=BOSS, muted_notifications={AdminNotification.MANUAL_PAYMENT})
    await make_admin_notifier(notifications, [boss]).notify_manual_payment(MANUAL)
    assert notifications.manual_payment_recipients == [BOSS]
