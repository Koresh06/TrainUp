from redis.asyncio import Redis

from src.application.interfaces.mailing_progress import (
    MailingProgressDTO,
    MailingProgressStore,
)

PROGRESS_TTL_SECONDS = 6 * 3600


class RedisMailingProgressStore(MailingProgressStore):
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    @staticmethod
    def _key(mailing_id: str) -> str:
        return f"mailing_result:{mailing_id}"

    async def add_batch_result(
        self, *, mailing_id: str, success: int, blocked: int, failed: int
    ) -> MailingProgressDTO:
        key = self._key(mailing_id)
        pipe = self._redis.pipeline()
        pipe.hincrby(key, "success", success)
        pipe.hincrby(key, "blocked", blocked)
        pipe.hincrby(key, "failed", failed)
        pipe.hincrby(key, "done_batches", 1)
        pipe.expire(key, PROGRESS_TTL_SECONDS)
        total_success, total_blocked, total_failed, done, _ = await pipe.execute()
        return MailingProgressDTO(
            done_batches=int(done),
            success=int(total_success),
            blocked=int(total_blocked),
            failed=int(total_failed),
        )

    async def clear(self, *, mailing_id: str) -> None:
        await self._redis.delete(self._key(mailing_id))
