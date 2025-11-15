"""Create build_suggestions table

Revision ID: 8e7b5e7c0f12
Revises: 232b6ca2fb3c
Create Date: 2025-11-12 22:19:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8e7b5e7c0f12"
down_revision: Union[str, None] = "232b6ca2fb3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "build_suggestions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("build", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_build_suggestions_user_id"), "build_suggestions", ["user_id"], unique=False)
    op.create_index("ix_build_suggestions_user_created_at", "build_suggestions", ["user_id", "created_at"], unique=False)
    op.create_index(op.f("ix_build_suggestions_created_at"), "build_suggestions", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_build_suggestions_created_at"), table_name="build_suggestions")
    op.drop_index("ix_build_suggestions_user_created_at", table_name="build_suggestions")
    op.drop_index(op.f("ix_build_suggestions_user_id"), table_name="build_suggestions")
    op.drop_table("build_suggestions")
