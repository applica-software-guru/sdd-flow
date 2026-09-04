import uuid

from app.models.audit_log_entry import AuditLogEntry
from app.repositories import AuditRepository


async def log_event(
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None,
    event_type: str,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    details: dict | None = None,
    audit_repo: AuditRepository = None,
    entity_label: str | None = None,
    summary: str | None = None,
) -> AuditLogEntry:
    """Append an immutable audit entry.

    `entity_label` and `summary` are denormalized at write time so entries stay
    human-readable even after the target entity is deleted or modified.
    """
    if audit_repo is None:
        audit_repo = AuditRepository()
    entry = AuditLogEntry(
        tenant_id=tenant_id,
        user_id=user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_label=entity_label,
        summary=summary,
        details=details or {},
    )
    return await audit_repo.create(entry)
