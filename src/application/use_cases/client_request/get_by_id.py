from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.client_request._shared import (
    ClientRequestDTO,
    ClientRequestEntity,
    _to_client_request_dto,
)
from src.domain.enums.request import ClientRequestKind
from src.domain.exception.consultation import ConsultationRequestNotFoundException
from src.domain.exception.feedback import FeedbackNotFoundException
from src.domain.exception.program import ProgramRequestNotFoundException
from src.domain.repositories.consultation import ConsultationRequestRepository
from src.domain.repositories.feedback import FeedbackRepository
from src.domain.repositories.program import ProgramRequestRepository


@dataclass(frozen=True, eq=False)
class GetClientRequestByIdRequest(UseCaseRequest):
    kind: ClientRequestKind
    request_id: int


@dataclass(kw_only=True)
class GetClientRequestByIdUseCase(UseCase[GetClientRequestByIdRequest, ClientRequestDTO]):
    program_repo: ProgramRequestRepository
    consultation_repo: ConsultationRequestRepository
    feedback_repo: FeedbackRepository

    async def __call__(self, command: GetClientRequestByIdRequest) -> ClientRequestDTO:
        request = await self.get_entity(command.kind, command.request_id)
        return _to_client_request_dto(command.kind, request)

    async def get_entity(
        self, kind: ClientRequestKind, request_id: int
    ) -> ClientRequestEntity:
        if kind == ClientRequestKind.PROGRAM:
            program = await self.program_repo.get_by_id(request_id)
            if program is None:
                raise ProgramRequestNotFoundException(request_id)
            return program
        if kind == ClientRequestKind.CONSULTATION:
            consultation = await self.consultation_repo.get_by_id(request_id)
            if consultation is None:
                raise ConsultationRequestNotFoundException(request_id)
            return consultation
        feedback = await self.feedback_repo.get_by_id(request_id)
        if feedback is None:
            raise FeedbackNotFoundException(request_id)
        return feedback
