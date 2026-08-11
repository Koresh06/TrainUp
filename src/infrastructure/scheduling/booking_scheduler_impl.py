from datetime import datetime

from src.application.interfaces.booking_scheduler import BookingScheduler
from src.application.interfaces.task_queue import TaskQueue
from src.domain.exception.booking import BookingNotFoundException
from src.domain.repositories.booking import BookingRepository


class BookingSchedulerImpl(BookingScheduler):
    def __init__(self, queue: TaskQueue, booking_repo: BookingRepository) -> None:
        self._queue = queue
        self._booking_repo = booking_repo

    async def schedule_training_reminder(
        self, *, booking_id: int, remind_at_utc: datetime
    ) -> None:
        booking = await self._booking_repo.get_by_id(booking_id)
        if booking is None:
            raise BookingNotFoundException(booking_id)

        job_id = await self._queue.schedule(
            task_name="send_training_reminder",
            args=(booking_id,),
            run_at_utc=remind_at_utc,
        )
        if job_id:
            booking.set_reminder_job(job_id)
            await self._booking_repo.save(booking)

    async def cancel_training_reminder(self, *, booking_id: int) -> None:
        booking = await self._booking_repo.get_by_id(booking_id)
        if booking is None:
            raise BookingNotFoundException(booking_id)

        if booking.reminder_job_id:
            await self._queue.cancel(job_id=booking.reminder_job_id)
            booking.clear_reminder_job()
            await self._booking_repo.save(booking)

    async def schedule_plan_next_training_reminder(
        self, *, client_id: int, remind_at_utc: datetime
    ) -> None:
        await self._queue.schedule(
            task_name="send_plan_next_training_reminder",
            args=(client_id,),
            run_at_utc=remind_at_utc,
        )