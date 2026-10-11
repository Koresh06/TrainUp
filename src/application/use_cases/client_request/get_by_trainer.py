from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.client_request._shared import (
    ClientRequestDTO,
    _to_client_request_dto,
)
from src.domain.enums.request import ClientRequestKind, RequestStatus
from src.domain.repositories.consultation import ConsultationRequestRepository
from src.domain.repositories.feedback import FeedbackRepository
from src.domain.repositories.program import ProgramRequestRepository


@dataclass(frozen=True, eq=False)
class GetClientRequestsByTrainerRequest(UseCaseRequest):
    trainer_id: int
    statuses: tuple[RequestStatus, ...] = (RequestStatus.NEW,)


@dataclass(kw_only=True)
class GetClientRequestsByTrainerUseCase(
    UseCase[GetClientRequestsByTrainerRequest, list[ClientRequestDTO]]
):
    program_repo: ProgramRequestRepository
    consultation_repo: ConsultationRequestRepository
    feedback_repo: FeedbackRepository

    async def __call__(
        self, command: GetClientRequestsByTrainerRequest
    ) -> list[ClientRequestDTO]:
        statuses = list(command.statuses)
        programs = await self.program_repo.get_by_trainer_id(command.trainer_id, statuses)
        consultations = await self.consultation_repo.get_by_trainer_id(
            command.trainer_id, statuses
        )
        feedback = await self.feedback_repo.get_by_trainer_id(command.trainer_id, statuses)

        result = [
            *(_to_client_request_dto(ClientRequestKind.PROGRAM, r) for r in programs),
            *(
                _to_client_request_dto(ClientRequestKind.CONSULTATION, r)
                for r in consultations
            ),
            *(_to_client_request_dto(ClientRequestKind.FEEDBACK, r) for r in feedback),
        ]
        result.sort(key=lambda r: r.created_at, reverse=True)
        return result
