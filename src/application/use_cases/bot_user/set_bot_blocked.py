import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.repositories.bot_user import BotUserRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class SetBotBlockedByUserRequest(UseCaseRequest):
    """Пользователь сам заблокировал/разблокировал бота (my_chat_member) —
    не путать с блокировкой пользователя админом (SetClientBlocked/SetTrainerBlocked)."""

    tg_id: int
    blocked: bool


@dataclass(kw_only=True)
class SetBotBlockedByUserUseCase(UseCase[SetBotBlockedByUserRequest, None]):
    bot_user_repo: BotUserRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: SetBotBlockedByUserRequest) -> None:
        await self.bot_user_repo.set_bot_blocked(
            tg_id=command.tg_id,
            blocked_at=datetime.now(timezone.utc) if command.blocked else None,
        )
        await self.transaction_manager.commit()
        logger.info(
            "[SetBotBlockedByUser:done] tg_id=%s blocked=%s", command.tg_id, command.blocked
        )
