from src.application.use_cases.booking.send_reminder import (
    SendTrainingReminderRequest,
    SendTrainingReminderUseCase,
)
from src.application.use_cases.calendar.maintain_calendar_buffer import (
    MaintainCalendarBufferUseCase,
    MaintainCalendarBufferRequest,
)


def register_taskiq_tasks(broker, *, container):

    @broker.task(
        task_name="maintain_calendar_buffer",
        schedule=[{"cron": "0 3 * * *"}],
    )
    async def maintain_calendar_buffer() -> None:
        async with container() as request_container:
            use_case = await request_container.get(MaintainCalendarBufferUseCase)
        await use_case(MaintainCalendarBufferRequest())

    @broker.task(task_name="send_training_reminder")
    async def send_training_reminder(booking_id: int) -> None:
        async with container() as request_container:
            use_case = await request_container.get(SendTrainingReminderUseCase)
        await use_case(SendTrainingReminderRequest(booking_id=booking_id))

    return {
        "maintain_calendar_buffer": maintain_calendar_buffer,
        "send_training_reminder": send_training_reminder,
    }
