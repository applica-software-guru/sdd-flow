"""add worker branch, job model, sync job type, entity nullable

Revision ID: h8c9d0e1f2a3
Revises: g7b8c9d0e1f2
Create Date: 2026-03-26T12:00:00.000Z
"""
from alembic import op


revision = "h8c9d0e1f2a3"
down_revision = "g7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add branch to workers
    op.execute("ALTER TABLE workers ADD COLUMN branch VARCHAR(200) NULL")

    # Add model to worker_jobs
    op.execute("ALTER TABLE worker_jobs ADD COLUMN model VARCHAR(100) NULL")

    # Add sync to job_type_enum
    op.execute("ALTER TYPE job_type_enum ADD VALUE 'sync'")

    # Make entity_type and entity_id nullable (sync jobs have no entity)
    op.execute("ALTER TABLE worker_jobs ALTER COLUMN entity_type DROP NOT NULL")
    op.execute("ALTER TABLE worker_jobs ALTER COLUMN entity_id DROP NOT NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE worker_jobs ALTER COLUMN entity_id SET NOT NULL")
    op.execute("ALTER TABLE worker_jobs ALTER COLUMN entity_type SET NOT NULL")
    op.execute("ALTER TABLE worker_jobs DROP COLUMN model")
    op.execute("ALTER TABLE workers DROP COLUMN branch")
    # Note: removing enum values from PostgreSQL requires recreating the type
