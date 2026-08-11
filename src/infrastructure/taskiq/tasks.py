from src.application.use_cases.calendar.maintain_calendar_buffer import MaintainCalendarBufferUseCase, MaintainCalendarBufferRequest
# from src.application.use_cases.send_training_reminder import SendTrainingReminderUseCase
# from src.application.use_cases.send_plan_next_training_reminder import (
#     SendPlanNextTrainingReminderUseCase,
# )


def register_taskiq_tasks(broker, *, container):

    @broker.task(
        task_name="maintain_calendar_buffer",
        schedule=[{"cron": "0 3 * * *"}],  # ежедневно в 03:00, cron-задача, без Scheduler
    )
    async def maintain_calendar_buffer() -> None:
        async with container() as request_container:
            use_case = await request_container.get(MaintainCalendarBufferUseCase)
        await use_case(MaintainCalendarBufferRequest())

    # @broker.task(task_name="send_training_reminder")
    # async def send_training_reminder(booking_id: int) -> None:
    #     async with container() as request_container:
    #         use_case = await request_container.get(SendTrainingReminderUseCase)
    #         await use_case.execute(booking_id=booking_id)

    # @broker.task(task_name="send_plan_next_training_reminder")
    # async def send_plan_next_training_reminder(client_id: int) -> None:
    #     async with container() as request_container:
    #         use_case = await request_container.get(SendPlanNextTrainingReminderUseCase)
    #         await use_case.execute(client_id=client_id)

    return {
        "maintain_calendar_buffer": maintain_calendar_buffer,
        # "send_training_reminder": send_training_reminder,
        # "send_plan_next_training_reminder": send_plan_next_training_reminder,
    }