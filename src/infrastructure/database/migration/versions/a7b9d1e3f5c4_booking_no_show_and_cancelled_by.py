"""booking: NO_SHOW status, cancelled_by / cancelled_at

Revision ID: a7b9d1e3f5c4
Revises: f1a3c5e7b902
Create Date: 2026-10-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b9d1e3f5c4'
down_revision: Union[str, Sequence[str], None] = 'f1a3c5e7b902'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

booking_actor = sa.Enum('TRAINER', 'CLIENT', 'SYSTEM', name='bookingactor')


def upgrade() -> None:
    """Upgrade schema."""
    # ADD VALUE нельзя использовать в той же транзакции — но здесь новое
    # значение только объявляется, данные с ним появятся позже
    op.execute("ALTER TYPE bookingstatus ADD VALUE IF NOT EXISTS 'NO_SHOW'")
    booking_actor.create(op.get_bind(), checkfirst=True)
    op.add_column('bookings', sa.Column('cancelled_by', booking_actor, nullable=True))
    op.add_column('bookings', sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True))
    # раздел «📋 Бронирования» стал «📅 Расписание» — FAQ уже засеян в базе
    op.execute(
        "UPDATE faq_items SET answer = replace(replace(answer, "
        "'📋 Бронирования → Текущие', '📅 Расписание → день'), "
        "'📋 Бронирования', '📅 Расписание')"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('bookings', 'cancelled_at')
    op.drop_column('bookings', 'cancelled_by')
    booking_actor.drop(op.get_bind(), checkfirst=True)
    # из enum Postgres значение не удалить — неявки становятся «проведёнными»,
    # а тип пересоздаётся без NO_SHOW
    op.execute("UPDATE bookings SET status = 'COMPLETED' WHERE status = 'NO_SHOW'")
    op.execute("ALTER TYPE bookingstatus RENAME TO bookingstatus_old")
    op.execute("CREATE TYPE bookingstatus AS ENUM ('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED')")
    op.execute(
        "ALTER TABLE bookings ALTER COLUMN status TYPE bookingstatus "
        "USING status::text::bookingstatus"
    )
    op.execute("DROP TYPE bookingstatus_old")
