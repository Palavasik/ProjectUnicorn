"""Initial schema: users and feedback tables.

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_user_id", name="users_telegram_user_id_key"),
        schema="public",
    )
    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("route_name", sa.Text(), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("distance_km", sa.Numeric(), nullable=True),
        sa.Column("start_lat", sa.Numeric(), nullable=True),
        sa.Column("start_lon", sa.Numeric(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_index("idx_feedback_telegram_user_id", "feedback", ["telegram_user_id"], schema="public")
    op.create_index("idx_feedback_created_at", "feedback", ["created_at"], schema="public")


def downgrade() -> None:
    op.drop_index("idx_feedback_created_at", table_name="feedback", schema="public")
    op.drop_index("idx_feedback_telegram_user_id", table_name="feedback", schema="public")
    op.drop_table("feedback", schema="public")
    op.drop_constraint("users_telegram_user_id_key", "users", type_="unique", schema="public")
    op.drop_table("users", schema="public")
