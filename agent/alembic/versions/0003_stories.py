"""stories table for the work slice

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-09
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="untriaged"),
        sa.Column("story_type", sa.String(16), nullable=True),
        sa.Column("priority", sa.String(4), nullable=True),
        sa.Column("triage_rationale", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("triaged_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_stories_status", "stories", ["status"])


def downgrade() -> None:
    op.drop_index("ix_stories_status", table_name="stories")
    op.drop_table("stories")
