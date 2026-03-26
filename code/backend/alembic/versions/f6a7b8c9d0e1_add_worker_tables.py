"""add worker tables

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-03-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE worker_status_enum AS ENUM ('online', 'offline', 'busy')")
    op.execute("CREATE TYPE job_status_enum AS ENUM ('queued', 'assigned', 'running', 'completed', 'failed', 'cancelled')")
    op.execute("CREATE TYPE message_kind_enum AS ENUM ('output', 'question', 'answer')")
    op.execute("""
        CREATE TABLE workers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            status worker_status_enum NOT NULL DEFAULT 'offline',
            agent VARCHAR(100) NOT NULL DEFAULT 'claude',
            last_heartbeat_at TIMESTAMPTZ,
            registered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            metadata JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_worker_project_name UNIQUE (project_id, name)
        )
    """)
    op.execute("""
        CREATE TABLE worker_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            worker_id UUID REFERENCES workers(id) ON DELETE SET NULL,
            entity_type VARCHAR(50) NOT NULL,
            entity_id UUID NOT NULL,
            status job_status_enum NOT NULL DEFAULT 'queued',
            prompt TEXT NOT NULL,
            agent VARCHAR(100) NOT NULL DEFAULT 'claude',
            exit_code INTEGER,
            created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_worker_jobs_project_status ON worker_jobs (project_id, status)")
    op.execute("""
        CREATE TABLE worker_job_messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID NOT NULL REFERENCES worker_jobs(id) ON DELETE CASCADE,
            kind message_kind_enum NOT NULL,
            content TEXT NOT NULL,
            sequence INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_worker_job_messages_job_sequence ON worker_job_messages (job_id, sequence)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS worker_job_messages")
    op.execute("DROP TABLE IF EXISTS worker_jobs")
    op.execute("DROP TABLE IF EXISTS workers")
    op.execute("DROP TYPE IF EXISTS message_kind_enum")
    op.execute("DROP TYPE IF EXISTS job_status_enum")
    op.execute("DROP TYPE IF EXISTS worker_status_enum")
