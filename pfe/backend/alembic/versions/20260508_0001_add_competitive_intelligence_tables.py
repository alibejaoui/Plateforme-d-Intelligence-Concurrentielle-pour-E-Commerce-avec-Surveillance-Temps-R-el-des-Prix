"""add competitive intelligence tables

Revision ID: 20260508_0001
Revises: 
Create Date: 2026-05-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260508_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # catalog_sources
    op.create_table(
        "catalog_sources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_url", sa.String(length=2000), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("config", sa.Text(), nullable=True),
    )
    op.create_index("idx_catalog_source_user_type", "catalog_sources", ["user_id", "source_type"])
    op.create_index(op.f("ix_catalog_sources_id"), "catalog_sources", ["id"])
    op.create_index(op.f("ix_catalog_sources_user_id"), "catalog_sources", ["user_id"])
    op.create_index(op.f("ix_catalog_sources_source_type"), "catalog_sources", ["source_type"])

    # import_jobs
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("catalog_source_id", sa.Integer(), sa.ForeignKey("catalog_sources.id"), nullable=False),
        sa.Column("status", sa.Enum("pending", "running", "completed", "failed", "cancelled", name="importjobstatus"), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
        sa.Column("stats", sa.JSON(), nullable=True),
    )
    op.create_index("idx_import_job_user_status", "import_jobs", ["user_id", "status"])
    op.create_index(op.f("ix_import_jobs_id"), "import_jobs", ["id"])
    op.create_index(op.f("ix_import_jobs_user_id"), "import_jobs", ["user_id"])
    op.create_index(op.f("ix_import_jobs_catalog_source_id"), "import_jobs", ["catalog_source_id"])
    op.create_index(op.f("ix_import_jobs_status"), "import_jobs", ["status"])
    op.create_index(op.f("ix_import_jobs_celery_task_id"), "import_jobs", ["celery_task_id"])

    # internal_products
    op.create_table(
        "internal_products",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("brand", sa.String(length=255), nullable=True),
        sa.Column("sku", sa.String(length=100), nullable=True),
        sa.Column("gtin", sa.String(length=32), nullable=True),
        sa.Column("category", sa.String(length=255), nullable=True),
        sa.Column("url", sa.String(length=2000), nullable=False),
        sa.Column("image_url", sa.String(length=2000), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="EUR"),
        sa.Column("availability", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index("idx_internal_product_user_sku", "internal_products", ["user_id", "sku"])
    op.create_index("idx_internal_product_user_gtin", "internal_products", ["user_id", "gtin"])
    op.create_index("idx_internal_product_user_category", "internal_products", ["user_id", "category"])
    op.create_index(op.f("ix_internal_products_id"), "internal_products", ["id"])
    op.create_index(op.f("ix_internal_products_user_id"), "internal_products", ["user_id"])
    op.create_index(op.f("ix_internal_products_name"), "internal_products", ["name"])
    op.create_index(op.f("ix_internal_products_brand"), "internal_products", ["brand"])
    op.create_index(op.f("ix_internal_products_sku"), "internal_products", ["sku"])
    op.create_index(op.f("ix_internal_products_gtin"), "internal_products", ["gtin"])
    op.create_index(op.f("ix_internal_products_category"), "internal_products", ["category"])

    # competitor_products
    op.create_table(
        "competitor_products",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("competitor_id", sa.Integer(), sa.ForeignKey("competitors.id"), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("brand", sa.String(length=255), nullable=True),
        sa.Column("sku", sa.String(length=100), nullable=True),
        sa.Column("gtin", sa.String(length=32), nullable=True),
        sa.Column("category", sa.String(length=255), nullable=True),
        sa.Column("url", sa.String(length=2000), nullable=False),
        sa.Column("image_url", sa.String(length=2000), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("availability", sa.String(length=50), nullable=True),
        sa.Column("raw", sa.Text(), nullable=True),
    )
    # utf8mb4: indexing full VARCHAR(2000) exceeds InnoDB max key length (~3072 bytes).
    op.create_index(
        "idx_competitor_product_competitor_url",
        "competitor_products",
        ["competitor_id", "url"],
        mysql_length={"url": 255},
    )
    op.create_index("idx_competitor_product_competitor_sku", "competitor_products", ["competitor_id", "sku"])
    op.create_index("idx_competitor_product_competitor_gtin", "competitor_products", ["competitor_id", "gtin"])
    op.create_index(op.f("ix_competitor_products_id"), "competitor_products", ["id"])
    op.create_index(op.f("ix_competitor_products_competitor_id"), "competitor_products", ["competitor_id"])
    op.create_index(op.f("ix_competitor_products_title"), "competitor_products", ["title"])
    op.create_index(op.f("ix_competitor_products_brand"), "competitor_products", ["brand"])
    op.create_index(op.f("ix_competitor_products_sku"), "competitor_products", ["sku"])
    op.create_index(op.f("ix_competitor_products_gtin"), "competitor_products", ["gtin"])
    op.create_index(op.f("ix_competitor_products_category"), "competitor_products", ["category"])

    # crawl_sessions
    op.create_table(
        "crawl_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("competitor_id", sa.Integer(), sa.ForeignKey("competitors.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.Enum("pending", "discovering", "extracting", "completed", "failed", "cancelled", name="crawlsessionstatus"), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("seed_url", sa.String(length=2000), nullable=True),
        sa.Column("config_snapshot", sa.Text(), nullable=True),
        sa.Column("stats", sa.JSON(), nullable=True),
        sa.Column("celery_group_id", sa.String(length=255), nullable=True),
    )
    op.create_index(op.f("ix_crawl_sessions_id"), "crawl_sessions", ["id"])
    op.create_index(op.f("ix_crawl_sessions_competitor_id"), "crawl_sessions", ["competitor_id"])
    op.create_index(op.f("ix_crawl_sessions_user_id"), "crawl_sessions", ["user_id"])
    op.create_index(op.f("ix_crawl_sessions_status"), "crawl_sessions", ["status"])
    op.create_index(op.f("ix_crawl_sessions_celery_group_id"), "crawl_sessions", ["celery_group_id"])

    # crawl_session_items
    op.create_table(
        "crawl_session_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("crawl_session_id", sa.Integer(), sa.ForeignKey("crawl_sessions.id"), nullable=False),
        sa.Column("competitor_product_id", sa.Integer(), sa.ForeignKey("competitor_products.id"), nullable=False),
        sa.Column("discovered_url", sa.String(length=2000), nullable=True),
    )
    op.create_index("idx_crawl_item_session_product", "crawl_session_items", ["crawl_session_id", "competitor_product_id"])
    op.create_index(op.f("ix_crawl_session_items_id"), "crawl_session_items", ["id"])
    op.create_index(op.f("ix_crawl_session_items_crawl_session_id"), "crawl_session_items", ["crawl_session_id"])
    op.create_index(op.f("ix_crawl_session_items_competitor_product_id"), "crawl_session_items", ["competitor_product_id"])

    # crawl_errors
    op.create_table(
        "crawl_errors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("crawl_session_id", sa.Integer(), sa.ForeignKey("crawl_sessions.id"), nullable=False),
        sa.Column("stage", sa.String(length=50), nullable=False),
        sa.Column("url", sa.String(length=2000), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
    )
    op.create_index("idx_crawl_error_session_stage", "crawl_errors", ["crawl_session_id", "stage"])
    op.create_index(op.f("ix_crawl_errors_id"), "crawl_errors", ["id"])
    op.create_index(op.f("ix_crawl_errors_crawl_session_id"), "crawl_errors", ["crawl_session_id"])
    op.create_index(op.f("ix_crawl_errors_stage"), "crawl_errors", ["stage"])

    # product_matches
    op.create_table(
        "product_matches",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("internal_product_id", sa.Integer(), sa.ForeignKey("internal_products.id"), nullable=False),
        sa.Column("competitor_product_id", sa.Integer(), sa.ForeignKey("competitor_products.id"), nullable=False),
        sa.Column("competitor_id", sa.Integer(), sa.ForeignKey("competitors.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("matching_method", sa.String(length=50), nullable=False),
        sa.Column("explanation", sa.JSON(), nullable=True),
        sa.UniqueConstraint("internal_product_id", "competitor_product_id", name="ux_match_internal_competitor_product"),
    )
    op.create_index("idx_match_competitor_confidence", "product_matches", ["competitor_id", "confidence_score"])
    op.create_index(op.f("ix_product_matches_id"), "product_matches", ["id"])
    op.create_index(op.f("ix_product_matches_internal_product_id"), "product_matches", ["internal_product_id"])
    op.create_index(op.f("ix_product_matches_competitor_product_id"), "product_matches", ["competitor_product_id"])
    op.create_index(op.f("ix_product_matches_competitor_id"), "product_matches", ["competitor_id"])
    op.create_index(op.f("ix_product_matches_user_id"), "product_matches", ["user_id"])
    op.create_index(op.f("ix_product_matches_confidence_score"), "product_matches", ["confidence_score"])
    op.create_index(op.f("ix_product_matches_matching_method"), "product_matches", ["matching_method"])

    # missing_products
    op.create_table(
        "missing_products",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("competitor_id", sa.Integer(), sa.ForeignKey("competitors.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("competitor_product_id", sa.Integer(), sa.ForeignKey("competitor_products.id"), nullable=False),
        sa.Column("opportunity_score", sa.Float(), nullable=True),
        sa.Column("reason", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.UniqueConstraint("competitor_id", "competitor_product_id", name="ux_missing_competitor_product"),
    )
    op.create_index(op.f("ix_missing_products_id"), "missing_products", ["id"])
    op.create_index(op.f("ix_missing_products_competitor_id"), "missing_products", ["competitor_id"])
    op.create_index(op.f("ix_missing_products_user_id"), "missing_products", ["user_id"])
    op.create_index(op.f("ix_missing_products_competitor_product_id"), "missing_products", ["competitor_product_id"])
    op.create_index(op.f("ix_missing_products_opportunity_score"), "missing_products", ["opportunity_score"])
    op.create_index(op.f("ix_missing_products_reason"), "missing_products", ["reason"])

    # unmatched_internal_products
    op.create_table(
        "unmatched_internal_products",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("competitor_id", sa.Integer(), sa.ForeignKey("competitors.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("internal_product_id", sa.Integer(), sa.ForeignKey("internal_products.id"), nullable=False),
        sa.Column("coverage_status", sa.String(length=50), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.UniqueConstraint("competitor_id", "internal_product_id", name="ux_unmatched_internal_competitor"),
    )
    op.create_index(op.f("ix_unmatched_internal_products_id"), "unmatched_internal_products", ["id"])
    op.create_index(op.f("ix_unmatched_internal_products_competitor_id"), "unmatched_internal_products", ["competitor_id"])
    op.create_index(op.f("ix_unmatched_internal_products_user_id"), "unmatched_internal_products", ["user_id"])
    op.create_index(op.f("ix_unmatched_internal_products_internal_product_id"), "unmatched_internal_products", ["internal_product_id"])
    op.create_index(op.f("ix_unmatched_internal_products_coverage_status"), "unmatched_internal_products", ["coverage_status"])


def downgrade() -> None:
    op.drop_table("unmatched_internal_products")
    op.drop_table("missing_products")
    op.drop_table("product_matches")
    op.drop_table("crawl_errors")
    op.drop_table("crawl_session_items")
    op.drop_table("crawl_sessions")
    op.drop_table("competitor_products")
    op.drop_table("internal_products")
    op.drop_table("import_jobs")
    op.drop_table("catalog_sources")
    # Note: MySQL doesn't support DROP TYPE for ENUM.
    # Alembic/SQLAlchemy handle ENUM cleanup where relevant.

