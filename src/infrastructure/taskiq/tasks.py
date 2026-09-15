from src.application.use_cases.recurring_booking.maintain import (
    MaintainRecurringBookingsRequest,
    MaintainRecurringBookingsUseCase,
)
from src.application.use_cases.booking.send_reminder import (
    SendTrainingReminderRequest,
    SendTrainingReminderUseCase,
)
from src.application.use_cases.calendar.maintain_calendar_buffer import (
    MaintainCalendarBufferUseCase,
    MaintainCalendarBufferRequest,
)
from src.application.use_cases.booking.mark_past_completed import (
    MarkPastBookingsCompletedRequest,
    MarkPastBookingsCompletedUseCase,
)
from src.domain.constants import RECURRING_BOOKINGS_TEST_MODE


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

    @broker.task(
        task_name="maintain_recurring_bookings",
        schedule=(
            [{"cron": "*/2 * * * *"}]
            if RECURRING_BOOKINGS_TEST_MODE
            else [{"cron": "0 4 * * *"}]
        ),
    )
    async def maintain_recurring_bookings() -> None:
        async with container() as request_container:
            use_case = await request_container.get(MaintainRecurringBookingsUseCase)
        await use_case(MaintainRecurringBookingsRequest())

    @broker.task(
        task_name="mark_past_bookings_completed",
        schedule=[{"cron": "0 * * * *"}], # каждый час
    )
    async def mark_past_bookings_completed() -> None:
        async with container() as request_container:
            use_case = await request_container.get(MarkPastBookingsCompletedUseCase)
        await use_case(MarkPastBookingsCompletedRequest())

    return {
        "maintain_calendar_buffer": maintain_calendar_buffer,
        "send_training_reminder": send_training_reminder,
        "maintain_recurring_bookings": maintain_recurring_bookings,
        "mark_past_bookings_completed": mark_past_bookings_completed,
    }
