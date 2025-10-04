"""add_template_id_to_habits

Revision ID: be20ad14af3d
Revises: 3601dd671d8f
Create Date: 2025-10-04 08:57:34.505528

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be20ad14af3d'
down_revision: Union[str, None] = '3601dd671d8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add template_id column to habits table."""
    op.add_column('habits', sa.Column('template_id', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove template_id column from habits table."""
    op.drop_column('habits', 'template_id')
