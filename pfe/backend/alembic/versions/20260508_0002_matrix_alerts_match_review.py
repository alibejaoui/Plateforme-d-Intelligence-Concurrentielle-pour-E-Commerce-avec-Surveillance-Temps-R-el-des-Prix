"""matrix, alerts engine, match review

Revision ID: 20260508_0002
Revises: 20260508_0001
Create Date: 2026-05-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260508_0002"
down_revision: Union[str, None] = "20260508_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("product_matches", sa.Column("review_status", sa.String(length=30), nullable=False, server_default="auto"))
    op.add_column("product_matches", sa.Column("review_note", sa.String(length=1000), nullable=True))
    op.add_column("product_matches", sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    op.add_column("product_matches", sa.Column("reviewed_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
    op.create_index(op.f("ix_product_matches_review_status"), "product_matches", ["review_status"])
    op.create_index(op.f("ix_product_matches_reviewed_by_user_id"), "product_matches", ["reviewed_by_user_id"])

    op.create_table(
        "alert_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("competitor_id", sa.Integer(), sa.ForeignKey("competitors.id"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("rule_type", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("threshold_value", sa.Float(), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
    )
    op.create_index("idx_alert_rules_user_type", "alert_rules", ["user_id", "rule_type"])
    op.create_index(op.f("ix_alert_rules_user_id"), "alert_rules", ["user_id"])
    op.create_index(op.f("ix_alert_rules_competitor_id"), "alert_rules", ["competitor_id"])
    op.create_index(op.f("ix_alert_rules_rule_type"), "alert_rules", ["rule_type"])
    op.create_index(op.f("ix_alert_rules_is_active"), "alert_rules", ["is_active"])

    op.create_table(
        "competitive_alerts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("competitor_id", sa.Integer(), sa.ForeignKey("competitors.id"), nullable=True),
        sa.Column("internal_product_id", sa.Integer(), sa.ForeignKey("internal_products.id"), nullable=True),
        sa.Column("competitor_product_id", sa.Integer(), sa.ForeignKey("competitor_products.id"), nullable=True),
        sa.Column("alert_rule_id", sa.Integer(), sa.ForeignKey("alert_rules.id"), nullable=True),
        sa.Column("alert_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
        sa.Column("signal_score", sa.Float(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("detected_at", sa.DateTime(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_comp_alerts_user_status", "competitive_alerts", ["user_id", "status"])
    op.create_index("idx_comp_alerts_user_type", "competitive_alerts", ["user_id", "alert_type"])
    op.create_index(op.f("ix_competitive_alerts_user_id"), "competitive_alerts", ["user_id"])
    op.create_index(op.f("ix_competitive_alerts_competitor_id"), "competitive_alerts", ["competitor_id"])
    op.create_index(op.f("ix_competitive_alerts_internal_product_id"), "competitive_alerts", ["internal_product_id"])
    op.create_index(op.f("ix_competitive_alerts_competitor_product_id"), "competitive_alerts", ["competitor_product_id"])
    op.create_index(op.f("ix_competitive_alerts_alert_rule_id"), "competitive_alerts", ["alert_rule_id"])
    op.create_index(op.f("ix_competitive_alerts_alert_type"), "competitive_alerts", ["alert_type"])
    op.create_index(op.f("ix_competitive_alerts_severity"), "competitive_alerts", ["severity"])
    op.create_index(op.f("ix_competitive_alerts_status"), "competitive_alerts", ["status"])


def downgrade() -> None:
    op.drop_table("competitive_alerts")
    op.drop_table("alert_rules")
    op.drop_index(op.f("ix_product_matches_reviewed_by_user_id"), table_name="product_matches")
    op.drop_index(op.f("ix_product_matches_review_status"), table_name="product_matches")
    op.drop_column("product_matches", "reviewed_by_user_id")
    op.drop_column("product_matches", "reviewed_at")
    op.drop_column("product_matches", "review_note")
    op.drop_column("product_matches", "review_status")

