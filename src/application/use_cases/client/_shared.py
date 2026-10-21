import secrets

from src.domain.entities.client import Client
from src.domain.exception.client import (
    ClientAccessDeniedException,
    ClientNotFoundException,
)
from src.domain.repositories.client import ClientRepository

# префикс deep-link'а персональной ссылки клиента — отличает её от общей
# ссылки тренера (у той токен из token_urlsafe, у этой — hex без «_»)
CLIENT_INVITE_PREFIX = "cl_"


def new_client_invite_token() -> str:
    return secrets.token_hex(10)


async def get_trainer_client(
    client_repo: ClientRepository, *, client_id: int, trainer_id: int
) -> Client:
    """Клиент тренера: чужой клиент — ошибка (callback можно подделать)."""
    client = await client_repo.get_by_id(client_id)
    if client is None:
        raise ClientNotFoundException(client_id=client_id)
    if client.trainer_id != trainer_id:
        raise ClientAccessDeniedException(client_id=client_id, trainer_id=trainer_id)
    return client
