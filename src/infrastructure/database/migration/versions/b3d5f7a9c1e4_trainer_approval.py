"""trainer approval status

Revision ID: b3d5f7a9c1e4
Revises: a9c1e3f5b7d2
Create Date: 2026-11-01 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3d5f7a9c1e4'
down_revision: Union[str, Sequence[str], None] = 'a9c1e3f5b7d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

approval_status = sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='trainerapprovalstatus')


def upgrade() -> None:
    """Upgrade schema."""
    approval_status.create(op.get_bind(), checkfirst=True)
    # уже работающие тренеры подтверждены: заявки касаются только новых
    op.add_column(
        'trainers',
        sa.Column('approval_status', approval_status, server_default='APPROVED', nullable=False),
    )
    op.create_index(op.f('ix__trainers_approval_status'), 'trainers', ['approval_status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix__trainers_approval_status'), table_name='trainers')
    op.drop_column('trainers', 'approval_status')
    approval_status.drop(op.get_bind(), checkfirst=True)
