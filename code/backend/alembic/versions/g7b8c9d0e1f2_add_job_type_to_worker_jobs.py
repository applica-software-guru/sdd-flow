"""add job_type to worker_jobs

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-03-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "g7b8c9d0e1f2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE job_type_enum AS ENUM ('apply', 'enrich')")
    op.execute(
        "ALTER TABLE worker_jobs ADD COLUMN job_type job_type_enum NOT NULL DEFAULT 'apply'"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE worker_jobs DROP COLUMN job_type")
    op.execute("DROP TYPE IF EXISTS job_type_enum")
