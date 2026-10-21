"""attendance confirmation the day before: booking fields and trainer setting

Revision ID: d2e4f6a8c0b1
Revises: c9d1f3a5b7e8
Create Date: 2026-10-21 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2e4f6a8c0b1'
down_revision: Union[str, Sequence[str], None] = 'c9d1f3a5b7e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('bookings', sa.Column('client_confirmed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('bookings', sa.Column('attendance_requested_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        'trainer_booking_settings',
        sa.Column('ask_attendance_confirmation', sa.Boolean(), server_default='true', nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('trainer_booking_settings', 'ask_attendance_confirmation')
    op.drop_column('bookings', 'attendance_requested_at')
    op.drop_column('bookings', 'client_confirmed_at')
