"""add number and slug to change_requests and bugs

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-24 00:00:00.000000

"""
import os
import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "untitled"


def _parse_path_prefix(path: str | None) -> tuple[int | None, str | None]:
    if not path:
        return None, None
    filename = os.path.basename(path)
    stem = filename[:-3] if filename.endswith(".md") else filename
    match = re.match(r"^(\d+)-(.+)$", stem)
    if match:
        return int(match.group(1)), match.group(2)
    return None, None


def upgrade() -> None:
    conn = op.get_bind()

    # --- change_requests ---
    op.add_column("change_requests", sa.Column("number", sa.Integer(), nullable=True))
    op.add_column("change_requests", sa.Column("slug", sa.String(512), nullable=True))

    # Back-fill: process rows ordered by created_at within each project
    rows = conn.execute(
        text("SELECT id, project_id, title, path FROM change_requests ORDER BY project_id, created_at ASC")
    ).fetchall()

    used_numbers: dict[str, set] = {}  # project_id -> set of numbers
    used_slugs: dict[str, set] = {}    # project_id -> set of slugs

    for row in rows:
        pid = str(row.project_id)
        used_numbers.setdefault(pid, set())
        used_slugs.setdefault(pid, set())

        path_number, path_slug = _parse_path_prefix(row.path)

        # Resolve number
        if path_number is not None and path_number not in used_numbers[pid]:
            number = path_number
        else:
            number = max(used_numbers[pid], default=0) + 1
            while number in used_numbers[pid]:
                number += 1
        used_numbers[pid].add(number)

        # Resolve slug
        base_slug = path_slug if path_slug else _slugify(row.title)
        slug = base_slug
        suffix = 2
        while slug in used_slugs[pid]:
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        used_slugs[pid].add(slug)

        conn.execute(
            text("UPDATE change_requests SET number = :n, slug = :s WHERE id = :id"),
            {"n": number, "s": slug, "id": row.id},
        )

    op.alter_column("change_requests", "number", nullable=False)
    op.alter_column("change_requests", "slug", nullable=False)
    op.create_unique_constraint("uq_cr_project_number", "change_requests", ["project_id", "number"])
    op.create_unique_constraint("uq_cr_project_slug", "change_requests", ["project_id", "slug"])

    # --- bugs ---
    op.add_column("bugs", sa.Column("number", sa.Integer(), nullable=True))
    op.add_column("bugs", sa.Column("slug", sa.String(512), nullable=True))

    rows = conn.execute(
        text("SELECT id, project_id, title, path FROM bugs ORDER BY project_id, created_at ASC")
    ).fetchall()

    used_numbers = {}
    used_slugs = {}

    for row in rows:
        pid = str(row.project_id)
        used_numbers.setdefault(pid, set())
        used_slugs.setdefault(pid, set())

        path_number, path_slug = _parse_path_prefix(row.path)

        if path_number is not None and path_number not in used_numbers[pid]:
            number = path_number
        else:
            number = max(used_numbers[pid], default=0) + 1
            while number in used_numbers[pid]:
                number += 1
        used_numbers[pid].add(number)

        base_slug = path_slug if path_slug else _slugify(row.title)
        slug = base_slug
        suffix = 2
        while slug in used_slugs[pid]:
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        used_slugs[pid].add(slug)

        conn.execute(
            text("UPDATE bugs SET number = :n, slug = :s WHERE id = :id"),
            {"n": number, "s": slug, "id": row.id},
        )

    op.alter_column("bugs", "number", nullable=False)
    op.alter_column("bugs", "slug", nullable=False)
    op.create_unique_constraint("uq_bug_project_number", "bugs", ["project_id", "number"])
    op.create_unique_constraint("uq_bug_project_slug", "bugs", ["project_id", "slug"])


def downgrade() -> None:
    op.drop_constraint("uq_bug_project_slug", "bugs", type_="unique")
    op.drop_constraint("uq_bug_project_number", "bugs", type_="unique")
    op.drop_column("bugs", "slug")
    op.drop_column("bugs", "number")

    op.drop_constraint("uq_cr_project_slug", "change_requests", type_="unique")
    op.drop_constraint("uq_cr_project_number", "change_requests", type_="unique")
    op.drop_column("change_requests", "slug")
    op.drop_column("change_requests", "number")
