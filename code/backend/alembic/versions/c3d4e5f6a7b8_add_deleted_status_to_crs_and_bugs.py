"""add deleted status to cr and bug enums

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-19

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE cr_status_enum ADD VALUE IF NOT EXISTS 'deleted'")
    op.execute("ALTER TYPE bug_status_enum ADD VALUE IF NOT EXISTS 'deleted'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from enums.
    # To fully revert, recreate the enum type (out of scope for this migration).
    pass
