"""add gtin to products for CI historical mapping

Revision ID: 20260508_0003
Revises: 20260508_0002
Create Date: 2026-05-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260508_0003"
down_revision: Union[str, None] = "20260508_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("gtin", sa.String(length=32), nullable=True))
    op.create_index("idx_product_gtin", "products", ["gtin"])


def downgrade() -> None:
    op.drop_index("idx_product_gtin", table_name="products")
    op.drop_column("products", "gtin")

