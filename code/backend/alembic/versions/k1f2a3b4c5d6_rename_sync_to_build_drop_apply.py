"""rename sync to build, drop apply job type

Revision ID: k1f2a3b4c5d6
Revises: j0e1f2a3b4c5
Create Date: 2026-03-27T00:00:00.000Z
"""
from alembic import op

revision = "k1f2a3b4c5d6"
down_revision = "j0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the default first (it depends on the enum type)
    op.execute("ALTER TABLE worker_jobs ALTER COLUMN job_type DROP DEFAULT")
    op.execute("ALTER TABLE worker_jobs ALTER COLUMN job_type TYPE VARCHAR(20)")
    op.execute("DROP TYPE job_type_enum")
    op.execute("UPDATE worker_jobs SET job_type = 'build' WHERE job_type = 'sync'")
    op.execute("DELETE FROM worker_jobs WHERE job_type = 'apply'")
    op.execute("CREATE TYPE job_type_enum AS ENUM ('enrich', 'build', 'custom')")
    op.execute(
        "ALTER TABLE worker_jobs ALTER COLUMN job_type TYPE job_type_enum "
        "USING job_type::job_type_enum"
    )
    op.execute("ALTER TABLE worker_jobs ALTER COLUMN job_type SET DEFAULT 'build'")


def downgrade() -> None:
    op.execute("ALTER TABLE worker_jobs ALTER COLUMN job_type DROP DEFAULT")
    op.execute("ALTER TABLE worker_jobs ALTER COLUMN job_type TYPE VARCHAR(20)")
    op.execute("DROP TYPE job_type_enum")
    op.execute("UPDATE worker_jobs SET job_type = 'sync' WHERE job_type = 'build'")
    op.execute("CREATE TYPE job_type_enum AS ENUM ('apply', 'enrich', 'sync', 'custom')")
    op.execute(
        "ALTER TABLE worker_jobs ALTER COLUMN job_type TYPE job_type_enum "
        "USING job_type::job_type_enum"
    )
    op.execute("ALTER TABLE worker_jobs ALTER COLUMN job_type SET DEFAULT 'apply'")
