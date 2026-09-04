import uuid

from app.models.audit_log_entry import AuditLogEntry
from app.models.tenant_member import TenantMember
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


async def log_event_for_user_tenants(
    user_id: uuid.UUID,
    event_type: str,
    tenant_ids: list[uuid.UUID] | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    details: dict | None = None,
    audit_repo: AuditRepository = None,
    entity_label: str | None = None,
    summary: str | None = None,
) -> None:
    """Append an audit entry for each tenant the user belongs to.

    Profile-level events (display name change, password change) are not scoped
    to a single tenant, so they are recorded in every tenant the user is a
    member of to keep the per-tenant audit log complete. When `tenant_ids` is
    omitted, the memberships are resolved here from the user id.
    """
    if tenant_ids is None:
        memberships = await TenantMember.find({"userId": user_id}).to_list()
        tenant_ids = [m.tenant_id for m in memberships]
    for tenant_id in tenant_ids:
        await log_event(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_label=entity_label,
            summary=summary,
            details=details or {},
            audit_repo=audit_repo,
        )
