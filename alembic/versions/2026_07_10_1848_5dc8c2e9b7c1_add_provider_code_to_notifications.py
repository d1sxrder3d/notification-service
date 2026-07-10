"""add provider_code to notifications

Revision ID: 5dc8c2e9b7c1
Revises: c7a42d86f371
Create Date: 2026-07-10 18:48:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5dc8c2e9b7c1'
down_revision: Union[str, Sequence[str], None] = 'c7a42d86f371'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'notifications',
        sa.Column('provider_code', sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('notifications', 'provider_code')
