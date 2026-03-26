import uuid
from datetime import timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bug import Bug
from app.models.change_request import ChangeRequest
from app.models.comment import Comment
from app.models.document_file import DocumentFile
from app.models.user import User


async def _fetch_comments(db: AsyncSession, entity_type: str, entity_id: uuid.UUID) -> str:
    """Fetch comments with author and timestamp, return formatted section or empty string."""
    result = await db.execute(
        select(Comment)
        .where(Comment.entity_type == entity_type, Comment.entity_id == entity_id)
        .order_by(Comment.created_at.asc())
    )
    comments = result.scalars().all()
    if not comments:
        return ""

    lines = ["\n\n---\n\n## Comments\n"]
    for c in comments:
        author_result = await db.execute(select(User.display_name).where(User.id == c.author_id))
        author = author_result.scalar_one_or_none() or "Unknown"
        ts = c.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines.append(f"**{author}** ({ts}):\n{c.body}\n")

    return "\n".join(lines)


def _branch_note(branch: str | None) -> str:
    if not branch:
        return ""
    return f"\n> **Working branch:** Make sure you are on branch `{branch}` before making any changes.\n"


async def generate_worker_prompt(
    db: AsyncSession,
    project_id: uuid.UUID,
    entity_type: str | None,
    entity_id: uuid.UUID | None,
    job_type: str = "apply",
    branch: str | None = None,
) -> str:
    """Generate a full agent prompt for the given job type and entity."""

    branch_note = _branch_note(branch)

    # ── sync job: project-level, no entity ───────────────────────────────────
    if job_type == "sync" or (entity_type is None and entity_id is None):
        return (
            f"Run `sdd pull`, then run the `sdd` skill, then run `sdd push`.\n"
            f"{branch_note}"
        )

    # ── entity-scoped jobs ────────────────────────────────────────────────────
    if entity_type == "change_request":
        result = await db.execute(
            select(ChangeRequest).where(
                ChangeRequest.id == entity_id,
                ChangeRequest.project_id == project_id,
            )
        )
        entity = result.scalar_one_or_none()
        if not entity:
            raise ValueError(f"Change request {entity_id} not found")
        entity_section = (
            f"# Change Request: {entity.title}\n\n"
            f"Status: {entity.status.value}\n\n"
            f"{entity.body}"
        )
        kind_label = "change request"

    elif entity_type == "bug":
        result = await db.execute(
            select(Bug).where(
                Bug.id == entity_id,
                Bug.project_id == project_id,
            )
        )
        entity = result.scalar_one_or_none()
        if not entity:
            raise ValueError(f"Bug {entity_id} not found")
        entity_section = (
            f"# Bug: {entity.title}\n\n"
            f"Status: {entity.status.value}\n"
            f"Severity: {entity.severity.value}\n\n"
            f"{entity.body}"
        )
        kind_label = "bug report"

    elif entity_type == "document":
        result = await db.execute(
            select(DocumentFile).where(
                DocumentFile.id == entity_id,
                DocumentFile.project_id == project_id,
            )
        )
        entity = result.scalar_one_or_none()
        if not entity:
            raise ValueError(f"Document {entity_id} not found")
        entity_section = (
            f"# Document: {entity.title}\n\n"
            f"Path: {entity.path}\n"
            f"Status: {entity.status.value}\n\n"
            f"{entity.content}"
        )
        kind_label = "document"

    else:
        raise ValueError(f"Unknown entity_type: {entity_type}")

    # Comments (not available for documents)
    comments_section = ""
    if entity_type in ("change_request", "bug"):
        comments_section = await _fetch_comments(db, entity_type, entity_id)

    if job_type != "enrich":
        raise ValueError(f"Unsupported job_type for entity: {job_type}")

    if entity_type == "document":
        prompt = (
            f"sdd pull --docs-only\n\n"
            f"Enrich the following document. Find the local file at `{entity.path}` "  # type: ignore[possibly-undefined]
            f"and rewrite its content with the enriched version — more complete, "
            f"well-structured, and detailed enough to serve as authoritative reference.\n"
            f"Then run `sdd push`.\n"
            f"{branch_note}\n"
            f"---\n\n"
            f"{entity_section}"
        )
    else:
        prompt = (
            f"sdd pull --crs-only\n\n"
            f"Enrich the following Change Request draft. Find the corresponding local file "
            f"and rewrite its content with the enriched version — add technical details, "
            f"acceptance criteria, edge cases, and implementation hints.\n"
            f"Then run `sdd mark-drafts-enriched <file>` on that specific file only, "
            f"then run `sdd push`.\n"
            f"{branch_note}\n"
            f"---\n\n"
            f"{entity_section}"
            f"{comments_section}"
        )

    return prompt
