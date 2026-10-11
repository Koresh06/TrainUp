import logging
from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.client_answer import ClientAnswer
from src.domain.repositories.client_answer import ClientAnswerRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class UpdateClientAnswersRequest(UseCaseRequest):
    client_id: int
    answers: dict[str, list[str]]  # question_id (str) -> value


@dataclass(kw_only=True)
class UpdateClientAnswersUseCase(UseCase[UpdateClientAnswersRequest, list[ClientAnswer]]):
    """Клиент заново проходит вопросы анкеты — старые ответы полностью заменяются."""

    answer_repo: ClientAnswerRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: UpdateClientAnswersRequest) -> list[ClientAnswer]:
        await self.answer_repo.delete_by_client_id(command.client_id)
        saved = await self.answer_repo.save_many(
            [
                ClientAnswer(client_id=command.client_id, question_id=int(qid), value=value)
                for qid, value in command.answers.items()
            ]
        )
        await self.transaction_manager.commit()

        logger.info("[UpdateClientAnswers:done] client_id=%s", command.client_id)
        return saved
