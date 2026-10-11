from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.exception.faq import FaqItemNotFoundException
from src.domain.repositories.faq import FaqRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class DeactivateFaqItemRequest(UseCaseRequest):
    faq_id: int


@dataclass(kw_only=True)
class DeactivateFaqItemUseCase(UseCase[DeactivateFaqItemRequest, None]):
    faq_repo: FaqRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: DeactivateFaqItemRequest) -> None:
        item = await self.faq_repo.get_by_id(command.faq_id)
        if item is None:
            raise FaqItemNotFoundException(command.faq_id)

        item.is_active = False
        await self.faq_repo.save(item)
        await self.transaction_manager.commit()
