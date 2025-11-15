"""Add missing user columns and create login_history

Revision ID: 9d7f0d4f7b9e
Revises: 8e7b5e7c0f12
Create Date: 2025-11-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9d7f0d4f7b9e"
down_revision: Union[str, None] = "8e7b5e7c0f12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users: add columns to match current SQLAlchemy model
    op.add_column(
        "users",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "users",
        sa.Column("full_name", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("bio", sa.Text(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("profile_picture_url", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("preferences", sa.JSON(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "users",
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )

    # login_history table
    op.create_table(
        "login_history",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("login_timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_login_history_user_id"), "login_history", ["user_id"], unique=False)
    op.create_index(op.f("ix_login_history_login_timestamp"), "login_history", ["login_timestamp"], unique=False)



def downgrade() -> None:
    # Drop login_history
    op.drop_index(op.f("ix_login_history_login_timestamp"), table_name="login_history")
    op.drop_index(op.f("ix_login_history_user_id"), table_name="login_history")
    op.drop_table("login_history")

    # Drop added user columns
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
    op.drop_column("users", "preferences")
    op.drop_column("users", "profile_picture_url")
    op.drop_column("users", "bio")
    op.drop_column("users", "full_name")
    op.drop_column("users", "is_verified")
