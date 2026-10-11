from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class MailingProgressDTO:
    done_batches: int
    success: int
    blocked: int
    failed: int


class MailingProgressStore(Protocol):
    """Счётчики батчей одной рассылки (батчи выполняются разными воркерами)."""

    async def add_batch_result(
        self, *, mailing_id: str, success: int, blocked: int, failed: int
    ) -> MailingProgressDTO: ...

    async def clear(self, *, mailing_id: str) -> None: ...
