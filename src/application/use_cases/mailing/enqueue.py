import logging
from dataclasses import dataclass

from src.application.interfaces.task_queue import TaskQueue
from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.enums.mailing import MailingTarget

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class EnqueueMailingRequest(UseCaseRequest):
    target: MailingTarget
    from_chat_id: int
    message_id: int
    trainer_id: int | None = None  # для TRAINER_CLIENTS


@dataclass(kw_only=True)
class EnqueueMailingUseCase(UseCase[EnqueueMailingRequest, None]):
    task_queue: TaskQueue

    async def __call__(self, command: EnqueueMailingRequest) -> None:
        if command.target == MailingTarget.TRAINER_CLIENTS and command.trainer_id is None:
            raise ValueError("trainer_id required for TRAINER_CLIENTS mailing")

        await self.task_queue.enqueue(
            task_name="execute_mailing",
            args=(
                command.target.value,
                command.from_chat_id,
                command.message_id,
                command.trainer_id,
            ),
        )
        logger.info(
            "[EnqueueMailing] target=%s trainer_id=%s", command.target, command.trainer_id
        )
