"""bot users and daily activity for admin analytics

Revision ID: d5f2b8c41a7e
Revises: af71f1ec3e1b
Create Date: 2026-10-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5f2b8c41a7e'
down_revision: Union[str, Sequence[str], None] = 'af71f1ec3e1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'bot_users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tg_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.VARCHAR(length=255), nullable=True),
        sa.Column('first_name', sa.VARCHAR(length=255), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('blocked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk__bot_users')),
    )
    op.create_index(op.f('ix__bot_users_tg_id'), 'bot_users', ['tg_id'], unique=True)
    op.create_index(op.f('ix__bot_users_blocked_at'), 'bot_users', ['blocked_at'], unique=False)

    op.create_table(
        'bot_user_activity',
        sa.Column('tg_id', sa.BigInteger(), nullable=False),
        sa.Column('activity_date', sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint('tg_id', 'activity_date', name=op.f('pk__bot_user_activity')),
    )
    op.create_index(op.f('ix__bot_user_activity_activity_date'), 'bot_user_activity', ['activity_date'], unique=False)

    # уже зарегистрированные тренеры и клиенты — «пришли» в момент регистрации,
    # иначе вся аудитория до релиза аналитики выпала бы из «Всего пользователей»
    op.execute(
        """
        INSERT INTO bot_users (tg_id, first_name, username, created_at, updated_at)
        SELECT tg_id, MIN(first_name), MIN(username), MIN(created_at), MIN(created_at)
        FROM (
            SELECT tg_id, name AS first_name, NULL AS username, created_at FROM trainers
            UNION ALL
            SELECT tg_id, first_name, username, created_at FROM clients
        ) AS registered
        GROUP BY tg_id
        ON CONFLICT (tg_id) DO NOTHING
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix__bot_user_activity_activity_date'), table_name='bot_user_activity')
    op.drop_table('bot_user_activity')
    op.drop_index(op.f('ix__bot_users_blocked_at'), table_name='bot_users')
    op.drop_index(op.f('ix__bot_users_tg_id'), table_name='bot_users')
    op.drop_table('bot_users')
