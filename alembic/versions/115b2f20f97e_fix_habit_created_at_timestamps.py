"""fix_habit_created_at_timestamps

Revision ID: 115b2f20f97e
Revises: be20ad14af3d
Create Date: 2025-10-04 15:24:04.564379

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '115b2f20f97e'
down_revision: Union[str, None] = 'be20ad14af3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Update existing habits' created_at timestamps to match their challenge's start_date.
    This fixes the progress calculation bug for habits created before this migration.
    """
    # Update all habits to have created_at = their challenge's start_date
    op.execute("""
        UPDATE habits
        SET created_at = challenges.start_date
        FROM challenges
        WHERE habits.challenge_id = challenges.id
        AND habits.created_at > challenges.start_date
    """)


def downgrade() -> None:
    """
    No downgrade needed - we're fixing incorrect data.
    """
    pass
