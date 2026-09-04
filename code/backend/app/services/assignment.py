"""Assignment service: shared assign/unassign flow for CRs and bugs.

Validates the new assignee, updates the entity, appends the assignment
history row, writes the audit entry and notifies the new assignee.
"""

import uuid

from app.models.assignment_history import AssignmentHistory
from app.models.bug import Bug
from app.models.change_request import ChangeRequest
from app.repositories import AssignmentRepository
from app.services.audit import AuditService
from app.services.notifications import NotificationService
from app.services.users import UserService


class AssignmentService:
    def __init__(
        self,
        assignment_repo: AssignmentRepository,
        audit_service: AuditService,
        notification_service: NotificationService,
        user_service: UserService,
    ) -> None:
        self._assignment_repo = assignment_repo
        self._audit_service = audit_service
        self._notification_service = notification_service
        self._user_service = user_service

    async def record_initial_assignment(
        self,
        tenant_id: uuid.UUID,
        actor_user_id: uuid.UUID | None,
        entity: Bug | ChangeRequest,
        entity_kind: str,
    ) -> None:
        """Seed the assignment history when an entity is created with an assignee."""
        if entity.assignee_id is None:
            return
        await self._assignment_repo.create(
            AssignmentHistory(
                tenant_id=tenant_id,
                entity_type=entity_kind,
                entity_id=entity.id,
                assignee_id=entity.assignee_id,
                assigned_by=actor_user_id,
            )
        )

    async def history_for(self, entity_kind: str, entity_id: uuid.UUID) -> list[AssignmentHistory]:
        """Append-only assignment history for an entity (newest first)."""
        return await self._assignment_repo.find_by_entity(entity_kind, entity_id)

    async def apply_assignment(
        self,
        tenant_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        entity: Bug | ChangeRequest,
        entity_kind: str,
        new_assignee_id: uuid.UUID | None,
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
            await self._user_service.ensure_tenant_member(tenant_id, new_assignee_id)

        old_assignee_id = entity.assignee_id
        entity.assignee_id = new_assignee_id
        await entity.save()

        prefix = "cr" if entity_kind == "change_request" else "bug"
        noun = "CR" if entity_kind == "change_request" else "bug"

        if new_assignee_id is None:
            summary = "unassigned"
            details: dict[str, str | None] = {
                "old_assignee_id": str(old_assignee_id),
                "new_assignee_id": None,
            }
        else:
            brief = await self._user_service.resolve_user_brief(new_assignee_id)
            who = brief.display_name if brief else str(new_assignee_id)
            summary = f"assigned to {who}"
            details = {
                "old_assignee_id": str(old_assignee_id) if old_assignee_id else None,
                "new_assignee_id": str(new_assignee_id),
            }

        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            f"{prefix}.assigned",
            entity_kind,
            entity.id,
            details=details,
            entity_label=entity.title,
            summary=summary,
        )

        await self._assignment_repo.create(
            AssignmentHistory(
                tenant_id=tenant_id,
                entity_type=entity_kind,
                entity_id=entity.id,
                assignee_id=new_assignee_id,
                assigned_by=actor_user_id,
            )
        )

        if new_assignee_id is not None and new_assignee_id != actor_user_id:
            await self._notification_service.create_notification(
                new_assignee_id,
                tenant_id,
                f"{prefix}.assigned",
                entity_kind,
                entity.id,
                f"{noun} '{entity.title}' assigned to you",
            )

        return True
