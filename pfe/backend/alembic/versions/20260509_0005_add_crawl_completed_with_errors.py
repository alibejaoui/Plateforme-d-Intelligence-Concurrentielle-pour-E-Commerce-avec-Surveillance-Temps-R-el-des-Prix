"""add completed_with_errors status for crawl sessions

Revision ID: 20260509_0005
Revises: 20260508_0004
Create Date: 2026-05-09
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260509_0005"
down_revision: Union[str, None] = "20260508_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "mysql":
        return
    op.execute(
        """
        ALTER TABLE crawl_sessions
        MODIFY COLUMN status ENUM(
            'pending',
            'discovering',
            'extracting',
            'completed',
            'completed_with_errors',
            'failed',
            'cancelled'
        ) NOT NULL
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "mysql":
        return
    op.execute(
        """
        ALTER TABLE crawl_sessions
        MODIFY COLUMN status ENUM(
            'pending',
            'discovering',
            'extracting',
            'completed',
            'failed',
            'cancelled'
        ) NOT NULL
        """
    )
