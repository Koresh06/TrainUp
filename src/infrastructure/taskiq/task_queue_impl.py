import uuid
from datetime import datetime
from typing import Any

from src.application.interfaces.task_queue import TaskQueue


class TaskiqTaskQueue(TaskQueue):
    def __init__(self, broker, schedule_source) -> None:
        self._broker = broker
        self._schedule_source = schedule_source

    def _get_task(self, task_name: str):
        for full_name, task in self._broker.get_all_tasks().items():
            if full_name.endswith(f":{task_name}"):
                return task
        raise RuntimeError(f"Task '{task_name}' not found in broker registry.")

    async def enqueue(self, *, task_name: str, args: tuple[Any, ...]) -> str | None:
        job = await self._get_task(task_name).kiq(*args)
        return getattr(job, "task_id", None)

    async def schedule(
        self, *, task_name: str, args: tuple[Any, ...], run_at_utc: datetime
    ) -> str | None:
        task = self._get_task(task_name)
        schedule_id = str(uuid.uuid4())
        await (
            task.kicker()
            .with_schedule_id(schedule_id)
            .schedule_by_time(self._schedule_source, run_at_utc, *args)
        )
        return schedule_id

    async def cancel(self, *, job_id: str) -> None:
        await self._schedule_source.delete_schedule(job_id)