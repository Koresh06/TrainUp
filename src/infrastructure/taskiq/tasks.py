from src.application.use_cases.booking.mark_completed import MarkBookingCompletedRequest, MarkBookingCompletedUseCase
from src.application.use_cases.recurring_booking.maintain import (
    MaintainRecurringBookingsRequest,
    MaintainRecurringBookingsUseCase,
)
from src.application.use_cases.booking.send_plan_next_reminder import (
    SendPlanNextTrainingReminderRequest,
    SendPlanNextTrainingReminderUseCase,
)
from src.application.use_cases.booking.send_reminder import (
    SendTrainingReminderRequest,
    SendTrainingReminderUseCase,
)
from src.application.use_cases.calendar.maintain_calendar_buffer import (
    MaintainCalendarBufferUseCase,
    MaintainCalendarBufferRequest,
)
from src.application.use_cases.mailing.execute import (
    ExecuteMailingRequest,
    ExecuteMailingUseCase,
)
from src.application.use_cases.mailing.execute_batch import (
    ExecuteMailingBatchRequest,
    ExecuteMailingBatchUseCase,
)
from src.application.use_cases.subscription.check_expiring import (
    CheckExpiringSubscriptionsRequest,
    CheckExpiringSubscriptionsUseCase,
)
from src.application.use_cases.payment.confirm import (
    ConfirmPaymentRequest,
    ConfirmPaymentUseCase,
)
from src.application.use_cases.payment.reject import (
    RejectPaymentRequest,
    RejectPaymentUseCase,
)
from src.application.use_cases.booking.attendance import (
    SendAttendanceRequestsRequest,
    SendAttendanceRequestsUseCase,
)
from src.application.use_cases.digest.send_trainer_digests import (
    SendTrainerDigestsRequest,
    SendTrainerDigestsUseCase,
)
from src.domain.constants import RECURRING_BOOKINGS_TEST_MODE
from src.domain.enums.mailing import MailingTarget


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

    @broker.task(task_name="mark_booking_completed")
    async def mark_booking_completed(booking_id: int) -> None:
        async with container() as request_container:
            use_case = await request_container.get(MarkBookingCompletedUseCase)
            await use_case(MarkBookingCompletedRequest(booking_id=booking_id))

    @broker.task(task_name="send_plan_next_training_reminder")
    async def send_plan_next_training_reminder(client_id: int) -> None:
        async with container() as request_container:
            use_case = await request_container.get(SendPlanNextTrainingReminderUseCase)
            await use_case(SendPlanNextTrainingReminderRequest(client_id=client_id))

    @broker.task(
        task_name="check_expiring_subscriptions",
        schedule=[{"cron": "5 * * * *"}],
    )
    async def check_expiring_subscriptions() -> None:
        async with container() as request_container:
            use_case = await request_container.get(CheckExpiringSubscriptionsUseCase)
            await use_case(CheckExpiringSubscriptionsRequest())

    @broker.task(task_name="execute_mailing")
    async def execute_mailing(
        target: str,
        from_chat_id: int,
        message_id: int,
        trainer_id: int | None = None,
    ) -> None:
        async with container() as request_container:
            use_case = await request_container.get(ExecuteMailingUseCase)
            await use_case(
                ExecuteMailingRequest(
                    target=MailingTarget(target),
                    from_chat_id=from_chat_id,
                    message_id=message_id,
                    trainer_id=trainer_id,
                )
            )

    @broker.task(task_name="execute_mailing_batch")
    async def execute_mailing_batch(
        chat_ids: list[int],
        from_chat_id: int,
        message_id: int,
        total_batches: int,
        target_label: str,
        mailing_id: str,
    ) -> None:
        async with container() as request_container:
            use_case = await request_container.get(ExecuteMailingBatchUseCase)
            await use_case(
                ExecuteMailingBatchRequest(
                    chat_ids=chat_ids,
                    from_chat_id=from_chat_id,
                    message_id=message_id,
                    total_batches=total_batches,
                    target_label=target_label,
                    mailing_id=mailing_id,
                )
            )

    # платежи: webhook-сервис только ставит задачу, подтверждение — в воркере
    @broker.task(task_name="confirm_payment")
    async def confirm_payment(external_id: str) -> None:
        async with container() as request_container:
            use_case = await request_container.get(ConfirmPaymentUseCase)
            await use_case(ConfirmPaymentRequest(external_id=external_id))

    @broker.task(task_name="reject_payment")
    async def reject_payment(external_id: str) -> None:
        async with container() as request_container:
            use_case = await request_container.get(RejectPaymentUseCase)
            await use_case(RejectPaymentRequest(external_id=external_id))

    # у каждого тренера свой час сводки; запуск каждые 15 минут, а не раз в час:
    # scheduler, перезапущенный ровно в :00, пропускает cron текущей минуты —
    # и тренер остался бы без сводки. Дубли отсекает дата последней отправки
    @broker.task(
        task_name="send_trainer_digests",
        schedule=[{"cron": "*/15 * * * *"}],
    )
    async def send_trainer_digests() -> None:
        async with container() as request_container:
            use_case = await request_container.get(SendTrainerDigestsUseCase)
            await use_case(SendTrainerDigestsRequest())

    # накануне спрашиваем клиентов «придёте?» (за ~сутки до тренировки)
    @broker.task(
        task_name="send_attendance_requests",
        schedule=[{"cron": "*/30 * * * *"}],
    )
    async def send_attendance_requests() -> None:
        async with container() as request_container:
            use_case = await request_container.get(SendAttendanceRequestsUseCase)
            await use_case(SendAttendanceRequestsRequest())

    # @broker.task(
    #     task_name="mark_past_bookings_completed",
    #     schedule=[{"cron": "0 5 * * *"}],
    # )
    # async def mark_past_bookings_completed() -> None:
    #     async with container() as request_container:
    #         use_case = await request_container.get(MarkPastBookingsCompletedUseCase)
    #         await use_case(MarkPastBookingsCompletedRequest())

    return {
        "maintain_calendar_buffer": maintain_calendar_buffer,
        "send_training_reminder": send_training_reminder,
        "maintain_recurring_bookings": maintain_recurring_bookings,
        "mark_booking_completed": mark_booking_completed,
        "send_plan_next_training_reminder": send_plan_next_training_reminder,
        "check_expiring_subscriptions": check_expiring_subscriptions,
        "execute_mailing": execute_mailing,
        "execute_mailing_batch": execute_mailing_batch,
        "confirm_payment": confirm_payment,
        "reject_payment": reject_payment,
        "send_trainer_digests": send_trainer_digests,
        "send_attendance_requests": send_attendance_requests,
        # "mark_past_bookings_completed": mark_past_bookings_completed,
    }
