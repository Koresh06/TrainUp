from dataclasses import dataclass
from datetime import datetime, timezone

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.repositories.bot_user import BotUserRepository
from src.domain.utils import get_project_today
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class TrackUserActivityRequest(UseCaseRequest):
    tg_id: int
    username: str | None = None
    first_name: str | None = None


@dataclass(kw_only=True)
class TrackUserActivityUseCase(UseCase[TrackUserActivityRequest, None]):
    """Отметка «пользователь был в боте сегодня» — вызывается middleware не
    чаще раза в день на пользователя (см. ActivityTrackingMiddleware)."""

    bot_user_repo: BotUserRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: TrackUserActivityRequest) -> None:
        await self.bot_user_repo.touch_activity(
            tg_id=command.tg_id,
            username=command.username,
            first_name=command.first_name,
            now=datetime.now(timezone.utc),
            activity_date=get_project_today(),
        )
        await self.transaction_manager.commit()
