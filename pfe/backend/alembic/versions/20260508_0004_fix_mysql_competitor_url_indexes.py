"""fix MySQL index length on competitor_products.url

Revision ID: 20260508_0004
Revises: 20260508_0003
Create Date: 2026-05-08

utf8mb4 + VARCHAR(2000) cannot be fully indexed under InnoDB max key length.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260508_0004"
down_revision: Union[str, None] = "20260508_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "mysql":
        return

    insp = sa.inspect(bind)
    if not insp.has_table("competitor_products"):
        return

    existing = {ix["name"] for ix in insp.get_indexes("competitor_products")}

    if "ix_competitor_products_url" in existing:
        op.drop_index("ix_competitor_products_url", table_name="competitor_products")

    if "idx_competitor_product_competitor_url" in existing:
        op.drop_index("idx_competitor_product_competitor_url", table_name="competitor_products")

    op.create_index(
        "idx_competitor_product_competitor_url",
        "competitor_products",
        ["competitor_id", "url"],
        mysql_length={"url": 255},
    )


def downgrade() -> None:
    # Recreating full-width url indexes fails on MySQL utf8mb4; leave schema as-is.
    pass
