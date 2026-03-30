import uuid
from datetime import timezone
from typing import Optional

from app.models.user import User
from app.repositories import (
    ChangeRequestRepository,
    BugRepository,
    DocumentFileRepository,
    CommentRepository,
)


async def _fetch_comments(
    entity_type: str,
    entity_id: uuid.UUID,
    comment_repo: CommentRepository,
) -> str:
    """Fetch comments with author and timestamp, return formatted section or empty string."""
    comments = await comment_repo.find_by_entity(entity_type, entity_id)
    if not comments:
        return ""

    # Batch-load authors to avoid N+1
    user_ids = list({str(c.author_id) for c in comments})
    users = await User.find({"_id": {"$in": user_ids}}).to_list()
    users_by_id = {str(u.id): u for u in users}

    lines = ["\n\n---\n\n## Comments\n"]
    for c in comments:
        author_obj = users_by_id.get(str(c.author_id))
        author = author_obj.display_name if author_obj else "Unknown"
        ts = c.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines.append(f"**{author}** ({ts}):\n{c.body}\n")

    return "\n".join(lines)


_REPORT_SECTION = (
    "\n\n---\n\n"
    "## Report\n\n"
    "At the end of your work, provide a detailed report including:\n"
    "- What was done (files created, modified, enriched)\n"
    "- Actions taken for each item\n"
    "- Any issues encountered or decisions made"
)


async def generate_worker_prompt(
    project_id: uuid.UUID,
    entity_type: str | None,
    entity_id: uuid.UUID | None,
    job_type: str = "build",
    branch: str | None = None,
    cr_repo: Optional[ChangeRequestRepository] = None,
    bug_repo: Optional[BugRepository] = None,
    doc_repo: Optional[DocumentFileRepository] = None,
    comment_repo: Optional[CommentRepository] = None,
) -> str:
    """Generate a full agent prompt for the given job type and entity."""
    # Instantiate repos if not provided
    if cr_repo is None:
        cr_repo = ChangeRequestRepository()
    if bug_repo is None:
        bug_repo = BugRepository()
    if doc_repo is None:
        doc_repo = DocumentFileRepository()
    if comment_repo is None:
        comment_repo = CommentRepository()

    # ── build job: project-level, no entity ──────────────────────────────────
    if job_type == "build" or (entity_type is None and entity_id is None):
        return (
            "You are running a full SDD build for this project.\n\n"
            "## Workflow\n\n"
            "1. **Pull** — Run `sdd pull` to fetch the latest documentation, change requests, "
            "and bugs from the remote server.\n\n"
            "2. **Build** — Run the `sdd` skill. It handles the full development loop:\n"
            "   - Check for open bugs (`sdd bug open`) and fix them, then `sdd mark-bug-resolved`\n"
            "   - Check for pending change requests (`sdd cr pending`), apply them to the docs, "
            "then `sdd mark-cr-applied`\n"
            "   - Run `sdd sync` to see which documentation files need to be implemented in code\n"
            "   - Read the listed docs and implement the required changes inside `code/`\n"
            "   - Run `sdd mark-synced` then **commit immediately** "
            "(`git add -A && git commit -m \"sdd sync: ...\"`) — mandatory\n\n"
            "3. **Push** — Run `sdd push` to publish the updated code, documentation, "
            "and status transitions back to the remote.\n"
            f"{_REPORT_SECTION}"
        )

    # ── entity-scoped jobs ────────────────────────────────────────────────────
    if entity_type == "change_request":
        entity = await cr_repo.find_by_id(entity_id)
        if not entity or str(entity.project_id) != str(project_id):
            raise ValueError(f"Change request {entity_id} not found")
        entity_section = (
            f"# Change Request: {entity.title}\n\n"
            f"Status: {entity.status.value}\n\n"
            f"{entity.body}"
        )
        kind_label = "change request"

    elif entity_type == "bug":
        entity = await bug_repo.find_by_id(entity_id)
        if not entity or str(entity.project_id) != str(project_id):
            raise ValueError(f"Bug {entity_id} not found")
        entity_section = (
            f"# Bug: {entity.title}\n\n"
            f"Status: {entity.status.value}\n"
            f"Severity: {entity.severity.value}\n\n"
            f"{entity.body}"
        )
        kind_label = "bug report"

    elif entity_type == "document":
        entity = await doc_repo.find_by_id(entity_id)
        if not entity or str(entity.project_id) != str(project_id):
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
        comments_section = await _fetch_comments(entity_type, entity_id, comment_repo)

    if job_type != "enrich":
        raise ValueError(f"Unsupported job_type for entity: {job_type}")

    if entity_type == "document":
        prompt = (
            f"sdd pull --docs-only\n\n"
            f"Enrich the following document. Find the local file at `{entity.path}` "  # type: ignore[possibly-undefined]
            f"and rewrite its content with the enriched version — more complete, "
            f"well-structured, and detailed enough to serve as authoritative reference.\n"
            f"Then run `sdd push`.\n"
            f"---\n\n"
            f"{entity_section}"
            f"{_REPORT_SECTION}"
        )
    else:
        if entity_type == "change_request":
            pull_flag = "--crs-only"
            kind_label = "Change Request draft"
        else:  # bug
            pull_flag = "--bugs-only"
            kind_label = "Bug draft"

        prompt = (
            f"sdd pull {pull_flag}\n\n"
            f"Enrich the following {kind_label}. Find the corresponding local file "
            f"and rewrite its content with the enriched version — add technical details, "
            f"acceptance criteria, edge cases, and implementation hints.\n"
            f"Then run `sdd mark-drafts-enriched <file>` on that specific file only, "
            f"then run `sdd push`.\n"
            f"---\n\n"
            f"{entity_section}"
            f"{comments_section}"
            f"{_REPORT_SECTION}"
        )

    return prompt
