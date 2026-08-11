from taskiq_redis import RedisScheduleSource, RedisStreamBroker, RedisAsyncResultBackend
from src.core.config import settings

result_backend = RedisAsyncResultBackend(redis_url=settings.db.redis.taskiq_url)

from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError as RedisTimeoutError

broker = RedisStreamBroker(
    url=settings.db.redis.taskiq_url,
    xread_block=2000,
    idle_timeout=5000,
    socket_timeout=15,
    socket_connect_timeout=15,
    retry_on_timeout=True,
    retry_on_error=[ConnectionError, RedisTimeoutError],
    retry=Retry(ExponentialBackoff(), retries=5),
    health_check_interval=10,
).with_result_backend(result_backend)

schedule_source = RedisScheduleSource(settings.db.redis.taskiq_url)