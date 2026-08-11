from dishka import make_async_container
from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from src.core.dependencies.providers import make_base_providers
from src.infrastructure.taskiq.broker import broker, schedule_source
from src.infrastructure.taskiq.tasks import register_taskiq_tasks

container = make_async_container(*make_base_providers())

scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker), schedule_source],
)

register_taskiq_tasks(broker, container=container)

# запуск: taskiq scheduler src.scheduler:scheduler
