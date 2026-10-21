from dataclasses import dataclass

from src.application.use_cases.base import UseCase, UseCaseRequest
from src.application.use_cases.client._shared import get_trainer_client
from src.domain.entities.client import Client
from src.domain.enums.client import ClientEditableField
from src.domain.repositories.client import ClientRepository
from src.infrastructure.database.transaction_manager.base import TransactionManager


@dataclass(frozen=True, eq=False)
class UpdateClientFieldRequest(UseCaseRequest):
    trainer_id: int
    client_id: int
    field: ClientEditableField
    # None — очистить поле (кроме имени — оно обязательно)
    value: str | None


@dataclass(kw_only=True)
class UpdateClientFieldUseCase(UseCase[UpdateClientFieldRequest, Client]):
    client_repo: ClientRepository
    transaction_manager: TransactionManager

    async def __call__(self, command: UpdateClientFieldRequest) -> Client:
        client = await get_trainer_client(
            self.client_repo, client_id=command.client_id, trainer_id=command.trainer_id
        )
        value = (command.value or "").strip() or None
        if command.field == ClientEditableField.FIRST_NAME:
            if value is None:
                raise ValueError("first_name is required")
            client.first_name = value
        else:
            setattr(client, command.field.value, value)
        client.touch()

        saved = await self.client_repo.save(client)
        await self.transaction_manager.commit()
        return saved
