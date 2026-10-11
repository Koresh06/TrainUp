from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.faq import FaqItem
from src.domain.exception.faq import FaqItemNotFoundException
from src.domain.repositories.faq import FaqRepository


@dataclass(frozen=True, eq=False)
class GetFaqItemByIdRequest(UseCaseRequest):
    faq_id: int


@dataclass(kw_only=True)
class GetFaqItemByIdUseCase(UseCase[GetFaqItemByIdRequest, FaqItem]):
    faq_repo: FaqRepository

    async def __call__(self, command: GetFaqItemByIdRequest) -> FaqItem:
        item = await self.faq_repo.get_by_id(command.faq_id)
        if item is None:
            raise FaqItemNotFoundException(command.faq_id)
        return item
