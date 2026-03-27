"""add custom job type

Revision ID: j0e1f2a3b4c5
Revises: i9d0e1f2a3b4
Create Date: 2026-03-27T00:00:00.000Z
"""
from alembic import op

revision = "j0e1f2a3b4c5"
down_revision = "i9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE job_type_enum ADD VALUE 'custom'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly.
    # Recreate the type without 'custom' if a rollback is needed.
    op.execute("""
        ALTER TABLE worker_jobs
            ALTER COLUMN job_type TYPE VARCHAR(20);
        DROP TYPE job_type_enum;
        CREATE TYPE job_type_enum AS ENUM ('apply', 'enrich', 'sync');
        UPDATE worker_jobs SET job_type = 'sync' WHERE job_type = 'custom';
        ALTER TABLE worker_jobs
            ALTER COLUMN job_type TYPE job_type_enum USING job_type::job_type_enum;
    """)
