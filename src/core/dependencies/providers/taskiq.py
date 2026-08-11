from dishka import Provider, Scope, provide
from taskiq_redis import RedisScheduleSource, RedisStreamBroker

from src.domain.repositories.booking import BookingRepository
from src.application.interfaces.booking_scheduler import BookingScheduler
from src.application.interfaces.task_queue import TaskQueue
from src.infrastructure.taskiq.broker import broker as shared_broker
from src.infrastructure.taskiq.broker import schedule_source as shared_schedule_source
from src.infrastructure.taskiq.task_queue_impl import TaskiqTaskQueue
from src.infrastructure.scheduling.booking_scheduler_impl import BookingSchedulerImpl


class TaskiqProvider(Provider):
    @provide(scope=Scope.APP)
    def taskiq_broker(self) -> RedisStreamBroker:
        return shared_broker

    @provide(scope=Scope.APP)
    def schedule_source(self) -> RedisScheduleSource:
        return shared_schedule_source

    @provide(scope=Scope.REQUEST)
    def task_queue(
        self,
        taskiq_broker: RedisStreamBroker,
        schedule_source: RedisScheduleSource,
    ) -> TaskQueue:
        return TaskiqTaskQueue(taskiq_broker, schedule_source)

    @provide(scope=Scope.REQUEST)
    def booking_scheduler(
        self,
        task_queue: TaskQueue,
        booking_repo: BookingRepository,
    ) -> BookingScheduler:
        return BookingSchedulerImpl(
            queue=task_queue,
            booking_repo=booking_repo,
        )
