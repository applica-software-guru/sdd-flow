import uuid

from app.models.assignment_history import AssignmentHistory
from app.repositories import AssignmentRepository
from app.services.audit import log_event
from app.services.notifications import create_notification
from app.services.users import ensure_tenant_member, resolve_user_brief


async def record_initial_assignment(
    tenant_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    entity,
    entity_kind: str,
    audit_repo=None,
    history_repo: AssignmentRepository = None,
) -> None:
    """Seed the assignment history when an entity is created with an assignee."""
    if entity.assignee_id is None:
        return
    if history_repo is None:
        history_repo = AssignmentRepository()
    await history_repo.create(
        AssignmentHistory(
            tenant_id=tenant_id,
            entity_type=entity_kind,
            entity_id=entity.id,
            assignee_id=entity.assignee_id,
            assigned_by=actor_user_id,
        )
    )


async def apply_assignment(
    tenant_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    entity,
    entity_kind: str,
    new_assignee_id: uuid.UUID | None,
    audit_repo=None,
    history_repo: AssignmentRepository = None,
) -> bool:
    """Assign/unassign `entity` (a ChangeRequest or Bug) with full side effects.

    - validates the new assignee is an active tenant member (raises 404 otherwise)
    - no-op (returns False) when the assignee is unchanged
    - updates the entity, appends an `assignment_history` row, writes an
      `{prefix}.assigned` audit entry and notifies the new assignee
      (unless they are the actor; no notification on unassign)
    """
    if new_assignee_id == entity.assignee_id:
        return False

    if new_assignee_id is not None:
        await ensure_tenant_member(tenant_id, new_assignee_id)

    old_assignee_id = entity.assignee_id
    entity.assignee_id = new_assignee_id
    await entity.save()

    prefix = "cr" if entity_kind == "change_request" else "bug"
    noun = "CR" if entity_kind == "change_request" else "bug"

    if new_assignee_id is None:
        summary = "unassigned"
        details = {"old_assignee_id": str(old_assignee_id), "new_assignee_id": None}
    else:
        brief = await resolve_user_brief(new_assignee_id)
        who = brief.display_name if brief else str(new_assignee_id)
        summary = f"assigned to {who}"
        details = {
            "old_assignee_id": str(old_assignee_id) if old_assignee_id else None,
            "new_assignee_id": str(new_assignee_id),
        }

    await log_event(
        tenant_id,
        actor_user_id,
        f"{prefix}.assigned",
        entity_kind,
        entity.id,
        details=details,
        entity_label=entity.title,
        summary=summary,
        audit_repo=audit_repo,
    )

    if history_repo is None:
        history_repo = AssignmentRepository()
    await history_repo.create(
        AssignmentHistory(
            tenant_id=tenant_id,
            entity_type=entity_kind,
            entity_id=entity.id,
            assignee_id=new_assignee_id,
            assigned_by=actor_user_id,
        )
    )

    if new_assignee_id is not None and new_assignee_id != actor_user_id:
        await create_notification(
            new_assignee_id,
            tenant_id,
            f"{prefix}.assigned",
            entity_kind,
            entity.id,
            f"{noun} '{entity.title}' assigned to you",
        )

    return True
