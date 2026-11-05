"""client archived by trainer

Revision ID: c8e0a2b4d6f1
Revises: b3d5f7a9c1e4
Create Date: 2026-11-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8e0a2b4d6f1'
down_revision: Union[str, Sequence[str], None] = 'b3d5f7a9c1e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # тренер убрал клиента: карточка и история остаются (статистика, отчёты),
    # но в списках тренера клиента нет, а запись к тренеру закрыта
    op.add_column(
        'clients',
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('clients', 'archived_at')
