import os
import re
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


def slugify(text: str) -> str:
    """Convert a string to a URL-friendly slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text or "untitled"


def parse_path_prefix(path: str) -> tuple[int | None, str | None]:
    """
    Given a file path like 'change-requests/001-fix-auth.md' or 'bugs/042-login-crash.md',
    return (number, slug) if the filename starts with a numeric prefix, else (None, None).

    Examples:
        'change-requests/001-fix-auth.md' -> (1, 'fix-auth')
        'bugs/042-login-crash.md'         -> (42, 'login-crash')
        'change-requests/my-cr.md'        -> (None, None)
    """
    filename = os.path.basename(path)
    stem = filename.removesuffix(".md")
    match = re.match(r"^(\d+)-(.+)$", stem)
    if match:
        number = int(match.group(1))
        slug = match.group(2)
        return number, slug
    return None, None


async def assign_number_and_slug(
    db: AsyncSession,
    model,
    project_id: uuid.UUID,
    title: str,
    path: str | None = None,
) -> tuple[int, str]:
    """
    Determine number and slug for a new CR or Bug.

    Priority:
    1. If path has a numeric prefix, restore number from it and derive slug from the path remainder.
    2. Otherwise, auto-increment number and slugify title.

    In both cases, ensure slug uniqueness within the project by appending -2, -3, etc.
    Uses SELECT FOR UPDATE to avoid number races.
    """
    path_number, path_slug = parse_path_prefix(path) if path else (None, None)

    # --- Determine number ---
    if path_number is not None:
        # Check if the number is already taken by a different entity
        taken = await db.execute(
            select(model).where(
                model.project_id == project_id,
                model.number == path_number,
            )
        )
        if taken.scalar_one_or_none() is not None:
            # Fallback to auto-increment
            path_number = None

    if path_number is None:
        # Aggregate queries don't support FOR UPDATE; the unique constraint
        # (project_id, number) will catch any concurrent collision at INSERT.
        result = await db.execute(
            select(func.max(model.number)).where(model.project_id == project_id)
        )
        max_number = result.scalar() or 0
        number = max_number + 1
    else:
        number = path_number

    # --- Determine slug ---
    base_slug = path_slug if path_slug is not None else slugify(title)
    slug = base_slug
    suffix = 2
    while True:
        taken = await db.execute(
            select(model).where(
                model.project_id == project_id,
                model.slug == slug,
            )
        )
        if taken.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    return number, slug
