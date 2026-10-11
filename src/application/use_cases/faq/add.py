from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.faq import FaqItem
from src.domain.enums.faq import FaqAudience
from src.domain.repositories.faq import FaqRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class AddFaqItemRequest(UseCaseRequest):
    question: str
    answer: str
    audience: FaqAudience = FaqAudience.CLIENT


@dataclass(kw_only=True)
class AddFaqItemUseCase(UseCase[AddFaqItemRequest, FaqItem]):
    faq_repo: FaqRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: AddFaqItemRequest) -> FaqItem:
        existing = await self.faq_repo.get_active(command.audience)
        next_order = max((item.order for item in existing), default=-1) + 1

        saved = await self.faq_repo.save(
            FaqItem(
                question=command.question,
                answer=command.answer,
                order=next_order,
                audience=command.audience,
            )
        )
        await self.transaction_manager.commit()
        return saved
