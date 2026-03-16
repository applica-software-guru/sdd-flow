import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log_entry import AuditLogEntry


async def log_event(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None,
    event_type: str,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    details: dict | None = None,
) -> AuditLogEntry:
    entry = AuditLogEntry(
        tenant_id=tenant_id,
        user_id=user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(entry)
    await db.flush()
    return entry
