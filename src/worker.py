from dishka import make_async_container
from taskiq import TaskiqEvents, TaskiqState

from src.utils.logging import setup_logging
from src.core.dependencies.providers import make_base_providers
from src.infrastructure.taskiq.broker import broker
from src.infrastructure.taskiq.tasks import register_taskiq_tasks

container = make_async_container(*make_base_providers())


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def setup_worker(state: TaskiqState) -> None:
    setup_logging()
    register_taskiq_tasks(broker, container=container)


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown_worker(state: TaskiqState) -> None:
    await container.close()


# запуск: taskiq worker src.worker:broker
