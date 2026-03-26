"""add changed_files to worker_jobs

Revision ID: i9d0e1f2a3b4
Revises: h8c9d0e1f2a3
Create Date: 2026-03-26T13:00:00.000Z
"""
from alembic import op


revision = "i9d0e1f2a3b4"
down_revision = "h8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE worker_jobs ADD COLUMN changed_files JSONB NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE worker_jobs DROP COLUMN changed_files")
