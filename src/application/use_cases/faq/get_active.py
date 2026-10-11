from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.domain.entities.faq import FaqItem
from src.domain.enums.faq import FaqAudience
from src.domain.repositories.faq import FaqRepository


@dataclass(frozen=True, eq=False)
class GetActiveFaqItemsRequest(UseCaseRequest):
    audience: FaqAudience = FaqAudience.CLIENT


@dataclass(kw_only=True)
class GetActiveFaqItemsUseCase(UseCase[GetActiveFaqItemsRequest, list[FaqItem]]):
    faq_repo: FaqRepository

    async def __call__(self, command: GetActiveFaqItemsRequest) -> list[FaqItem]:
        return await self.faq_repo.get_active(command.audience)
