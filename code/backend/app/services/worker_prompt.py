import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bug import Bug
from app.models.change_request import ChangeRequest
from app.models.document_file import DocumentFile


async def generate_worker_prompt(
    db: AsyncSession,
    project_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    job_type: str = "apply",
) -> str:
    """Generate a full agent prompt from a CR or Bug plus all project documents."""

    # Fetch the target entity
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
    else:
        raise ValueError(f"Unknown entity_type: {entity_type}")

    # Fetch all project documents for context
    docs_result = await db.execute(
        select(DocumentFile).where(
            DocumentFile.project_id == project_id,
            DocumentFile.status != "deleted",
        ).order_by(DocumentFile.path)
    )
    docs = docs_result.scalars().all()

    docs_section = ""
    if docs:
        docs_section = "\n\n---\n\n# Project Documentation\n\n"
        for doc in docs:
            docs_section += f"## {doc.path}: {doc.title}\n\n{doc.content}\n\n"

    # Compose the full prompt
    if job_type == "enrich":
        prompt = (
            f"You are an AI agent helping to enrich a draft specification for a software project.\n\n"
            f"Your task is to expand and improve the following draft "
            f"{'change request' if entity_type == 'change_request' else 'bug report'} "
            f"so that it is detailed enough for a developer to implement without ambiguity.\n\n"
            f"Follow the SDD remote skill workflow:\n"
            f"1. Read the draft carefully\n"
            f"2. Enrich it: add technical details, acceptance criteria, implementation hints, "
            f"edge cases, and any other relevant information based on the project documentation\n"
            f"3. Run `sdd pull --crs-only` (or `--bugs-only`) to sync the latest state\n"
            f"4. Run `sdd drafts` to see all drafts\n"
            f"5. Update the local draft file with your enriched content\n"
            f"6. Run `sdd mark-drafts-enriched` to transition draft → pending/open\n"
            f"7. Run `sdd push` to push the enriched content back to SDD Flow\n\n"
            f"---\n\n"
            f"{entity_section}"
            f"{docs_section}"
        )
    else:
        prompt = (
            f"You are an AI agent working on a software project. "
            f"Your task is to implement the following {'change request' if entity_type == 'change_request' else 'bug fix'}.\n\n"
            f"Read the task description carefully, review the project documentation for context, "
            f"then implement the required changes.\n\n"
            f"---\n\n"
            f"{entity_section}"
            f"{docs_section}"
        )

    return prompt
