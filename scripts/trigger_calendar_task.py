"""
Временный скрипт для ручной проверки maintain_calendar_buffer,
без ожидания cron-расписания (03:00) и без необходимости поднимать scheduler.

Кладётся в корень проекта как scripts/trigger_calendar_task.py
(рядом с уже существующим scripts/seed.py).

Запуск:
    uv run python -m scripts.trigger_calendar_task

Требования:
    - worker должен быть запущен и слушать очередь (uv run taskiq worker src.worker:broker),
      иначе задача просто встанет в очередь и будет ждать, пока воркер её не заберёт.
    - в БД уже должен быть хотя бы один активный Trainer и активные SlotTemplate,
      иначе задача отработает "пусто" (см. лог [MaintainCalendarBuffer:skip]).

После использования можно удалить — это не часть боевого кода.
"""
import asyncio

from dishka import make_async_container

from src.core.dependencies.providers import make_base_providers
from src.infrastructure.taskiq.broker import broker
from src.infrastructure.taskiq.tasks import register_taskiq_tasks


async def main() -> None:
    container = make_async_container(*make_base_providers())
    tasks = register_taskiq_tasks(broker, container=container)

    job = await tasks["maintain_calendar_buffer"].kiq()
    print(f"Task enqueued: {getattr(job, 'task_id', job)}")
    print("Check worker logs for execution result "
          "([MaintainCalendarBuffer:done] or [MaintainCalendarBuffer:skip]).")


if __name__ == "__main__":
    asyncio.run(main())