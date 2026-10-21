"""offline clients: tg_id/phone/age/experience nullable, source, trainer note, invite token

Revision ID: f1a3c5e7b902
Revises: d5f2b8c41a7e
Create Date: 2026-10-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a3c5e7b902'
down_revision: Union[str, Sequence[str], None] = 'd5f2b8c41a7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

client_source = sa.Enum('TELEGRAM', 'MANUAL', name='clientsource')
sport_experience = sa.Enum(
    'NONE', 'UP_TO_3_MONTHS', 'UP_TO_6_MONTHS', 'MORE_THAN_YEAR', name='sport_experience'
)


def upgrade() -> None:
    """Upgrade schema."""
    client_source.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'clients',
        sa.Column('source', client_source, server_default='TELEGRAM', nullable=False),
    )
    op.add_column('clients', sa.Column('trainer_note', sa.VARCHAR(length=1000), nullable=True))
    op.add_column('clients', sa.Column('invite_token', sa.VARCHAR(length=64), nullable=True))
    op.create_index(op.f('ix__clients_invite_token'), 'clients', ['invite_token'], unique=True)

    # клиент без Telegram: тренер заполняет только имя
    op.alter_column('clients', 'tg_id', existing_type=sa.BigInteger(), nullable=True)
    op.alter_column('clients', 'phone', existing_type=sa.VARCHAR(length=255), nullable=True)
    op.alter_column('clients', 'age', existing_type=sa.Integer(), nullable=True)
    op.alter_column('clients', 'sport_experience', existing_type=sport_experience, nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # карточки без Telegram не переживут NOT NULL — откат их удаляет
    op.execute("DELETE FROM clients WHERE tg_id IS NULL")
    op.execute("UPDATE clients SET phone = '' WHERE phone IS NULL")
    op.execute("UPDATE clients SET age = 0 WHERE age IS NULL")
    op.execute("UPDATE clients SET sport_experience = 'NONE' WHERE sport_experience IS NULL")
    op.alter_column('clients', 'sport_experience', existing_type=sport_experience, nullable=False)
    op.alter_column('clients', 'age', existing_type=sa.Integer(), nullable=False)
    op.alter_column('clients', 'phone', existing_type=sa.VARCHAR(length=255), nullable=False)
    op.alter_column('clients', 'tg_id', existing_type=sa.BigInteger(), nullable=False)

    op.drop_index(op.f('ix__clients_invite_token'), table_name='clients')
    op.drop_column('clients', 'invite_token')
    op.drop_column('clients', 'trainer_note')
    op.drop_column('clients', 'source')
    client_source.drop(op.get_bind(), checkfirst=True)
