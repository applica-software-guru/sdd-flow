"""add path column to change_requests and bugs

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('change_requests', sa.Column('path', sa.String(1024), nullable=True))
    op.add_column('bugs', sa.Column('path', sa.String(1024), nullable=True))


def downgrade() -> None:
    op.drop_column('bugs', 'path')
    op.drop_column('change_requests', 'path')
