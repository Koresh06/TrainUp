"""feedback trainer and status, slots deactivation instead of blocking

Revision ID: b7d41e09c3a2
Revises: e2dd5c14c0c2
Create Date: 2026-10-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b7d41e09c3a2'
down_revision: Union[str, Sequence[str], None] = 'e2dd5c14c0c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


request_status = postgresql.ENUM(
    'NEW', 'IN_PROGRESS', 'DONE', 'REJECTED', name='requeststatus', create_type=False
)


def upgrade() -> None:
    """Upgrade schema."""
    # --- feedback_messages: привязка к тренеру + статус обработки вместо is_read ---
    op.add_column('feedback_messages', sa.Column('trainer_id', sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE feedback_messages fm
        SET trainer_id = c.trainer_id
        FROM clients c
        WHERE c.id = fm.client_id
        """
    )
    op.execute("DELETE FROM feedback_messages WHERE trainer_id IS NULL")
    op.alter_column('feedback_messages', 'trainer_id', nullable=False)
    op.create_index(op.f('ix__feedback_messages_trainer_id'), 'feedback_messages', ['trainer_id'], unique=False)
    op.create_foreign_key(op.f('feedback_messages_trainer_id_fkey'), 'feedback_messages', 'trainers', ['trainer_id'], ['id'], ondelete='CASCADE')

    op.add_column('feedback_messages', sa.Column('status', request_status, server_default='NEW', nullable=False))
    op.execute("UPDATE feedback_messages SET status = 'DONE' WHERE is_read")
    op.drop_column('feedback_messages', 'is_read')
    op.alter_column('feedback_messages', 'message', type_=sa.VARCHAR(length=1000), existing_nullable=True)

    # --- calendar_slots: время, убранное из шаблона, теперь is_active=false, а
    # BLOCKED — только ручная блокировка тренером. До этой версии ручной
    # блокировки не было, поэтому все BLOCKED-слоты — результат удаления времени
    # из шаблона. Если время с тех пор вернули в шаблон — слот снова доступен.
    op.execute(
        """
        UPDATE calendar_slots cs
        SET is_active = EXISTS (
                SELECT 1 FROM slot_templates st
                WHERE st.trainer_id = cs.trainer_id
                  AND st.weekday = EXTRACT(ISODOW FROM cs.slot_date)::int - 1
                  AND st.start_time = cs.start_time
                  AND st.is_active
            ),
            status = CASE
                WHEN (
                    SELECT count(*) FROM bookings b
                    WHERE b.slot_id = cs.id AND b.status IN ('PENDING', 'CONFIRMED')
                ) >= cs.capacity THEN 'BOOKED'::slotstatus
                ELSE 'FREE'::slotstatus
            END
        WHERE cs.status = 'BLOCKED'
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'feedback_messages', 'message', type_=sa.VARCHAR(length=255),
        existing_nullable=True, postgresql_using='left(message, 255)',
    )
    op.add_column('feedback_messages', sa.Column('is_read', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.execute("UPDATE feedback_messages SET is_read = (status = 'DONE')")
    op.drop_column('feedback_messages', 'status')
    op.drop_constraint(op.f('feedback_messages_trainer_id_fkey'), 'feedback_messages', type_='foreignkey')
    op.drop_index(op.f('ix__feedback_messages_trainer_id'), table_name='feedback_messages')
    op.drop_column('feedback_messages', 'trainer_id')
