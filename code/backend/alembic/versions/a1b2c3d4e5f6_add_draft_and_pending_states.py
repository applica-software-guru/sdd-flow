"""add draft and pending states

Revision ID: a1b2c3d4e5f6
Revises: 69d9f5ff4df9
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '69d9f5ff4df9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'draft' to doc_status_enum
    op.execute("ALTER TYPE doc_status_enum ADD VALUE IF NOT EXISTS 'draft' BEFORE 'new'")
    # Add 'draft' to bug_status_enum
    op.execute("ALTER TYPE bug_status_enum ADD VALUE IF NOT EXISTS 'draft' BEFORE 'open'")
    # Add 'pending' to cr_status_enum
    op.execute("ALTER TYPE cr_status_enum ADD VALUE IF NOT EXISTS 'pending' AFTER 'draft'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from enums directly.
    # A full enum recreation would be needed for a proper downgrade.
    # For safety, this is left as a no-op — the extra enum values are harmless.
    pass
