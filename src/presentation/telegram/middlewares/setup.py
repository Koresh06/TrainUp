from aiogram import Dispatcher

from src.presentation.telegram.features import (
    ADMIN_DIALOGS,
    CLIENT_DIALOGS,
    TRAINER_CABINET_DIALOGS,
)
from src.presentation.telegram.middlewares.activity import ActivityTrackingMiddleware
from src.presentation.telegram.middlewares.access import (
    AdminGuard,
    ClientTrainerGuard,
    TrainerSubscriptionGuard,
    UserAccessMiddleware,
)


def setup_middlewares(dp: Dispatcher) -> None:
    """Вызывать ПОСЛЕ setup_dishka: UserAccessMiddleware берёт контейнер из data."""
    # активность — раньше проверки доступа: заблокированный админом тоже «заходил»
    activity = ActivityTrackingMiddleware()
    dp.message.outer_middleware(activity)
    dp.callback_query.outer_middleware(activity)

    access = UserAccessMiddleware()
    dp.message.outer_middleware(access)
    dp.callback_query.outer_middleware(access)

    for guard, dialogs in (
        (TrainerSubscriptionGuard(), TRAINER_CABINET_DIALOGS),
        (ClientTrainerGuard(), CLIENT_DIALOGS),
        (AdminGuard(), ADMIN_DIALOGS),
    ):
        for dialog in dialogs:
            dialog.message.middleware(guard)
            dialog.callback_query.middleware(guard)
