"""Change Request domain service.

Owns all CR data access and business flows. Mirrors `BugService`.
"""

import math
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status

from app.models.change_request import ChangeRequest, CRStatus
from app.models.comment import Comment, EntityType
from app.repositories import (
    ChangeRequestRepository,
    CommentRepository,
)
from app.schemas.change_requests import (
    AssignmentEntryResponse,
    CRCreate,
    CRListResponse,
    CRResponse,
    CRTransition,
    CRUpdate,
)
from app.schemas.comments import CommentCreate, CommentResponse
from app.services.assignment import AssignmentService
from app.services.audit import AuditService
from app.services.collab_notifications import CollaborationService
from app.services.notifications import NotificationService
from app.services.numbering import NumberingService
from app.services.projects import ProjectService
from app.services.slug import slugify
from app.services.users import UserService


class ChangeRequestService:
    def __init__(
        self,
        project_service: ProjectService,
        cr_repo: ChangeRequestRepository,
        comment_repo: CommentRepository,
        user_service: UserService,
        audit_service: AuditService,
        notification_service: NotificationService,
        assignment_service: AssignmentService,
        collaboration_service: CollaborationService,
        numbering_service: NumberingService,
    ) -> None:
        self._project_service = project_service
        self._cr_repo = cr_repo
        self._comment_repo = comment_repo
        self._user_service = user_service
        self._audit_service = audit_service
        self._notification_service = notification_service
        self._assignment_service = assignment_service
        self._collaboration_service = collaboration_service
        self._numbering_service = numbering_service

    # ── helpers ───────────────────────────────────────────────────────────────

    async def _get_cr_in_project_or_404(
        self, project_id: uuid.UUID, cr_id: uuid.UUID
    ) -> ChangeRequest:
        cr = await self._cr_repo.find_by_id(cr_id)
        if cr is None or cr.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found"
            )
        return cr

    async def _enrich(
        self, responses: list[CRResponse], entities: list[ChangeRequest]
    ) -> list[CRResponse]:
        """Attach resolved author/assignee UserBrief and batched comments_count (no N+1)."""
        if not responses:
            return responses
        user_ids: set[uuid.UUID] = set()
        for e in entities:
            user_ids.add(e.author_id)
            if e.assignee_id is not None:
                user_ids.add(e.assignee_id)
        users = await self._user_service.resolve_user_briefs(user_ids)

        cr_ids = [e.id for e in entities]
        comment_counts = await self._comment_repo.count_by_entities(
            EntityType.change_request.value, cr_ids
        )

        for resp, e in zip(responses, entities):
            resp.author = users.get(e.author_id)
            resp.assignee = users.get(e.assignee_id) if e.assignee_id is not None else None
            resp.comments_count = comment_counts.get(e.id, 0)
        return responses

    async def _single(self, cr: ChangeRequest) -> CRResponse:
        return (await self._enrich([CRResponse.model_validate(cr)], [cr]))[0]

    # ── CRUD ──────────────────────────────────────────────────────────────────

    async def create_cr(
        self,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        body: CRCreate,
        actor_user_id: uuid.UUID,
    ) -> CRResponse:
        await self._project_service.get_project_or_404(tenant_id, project_id)
        if body.assignee_id is not None:
            await self._user_service.ensure_tenant_member(tenant_id, body.assignee_id)

        cr = ChangeRequest(
            project_id=project_id,
            number=0,
            slug="",
            title=body.title,
            body=body.body,
            author_id=actor_user_id,
            assignee_id=body.assignee_id,
            target_files=body.target_files or [],
        )
        await self._numbering_service.assign_number_and_slug(
            cr, project_id, body.title, explicit_slug=body.slug
        )

        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            "cr.created",
            "change_request",
            cr.id,
            entity_label=cr.title,
            summary="created",
        )
        await self._assignment_service.record_initial_assignment(
            tenant_id, actor_user_id, cr, "change_request"
        )

        if body.assignee_id and body.assignee_id != actor_user_id:
            await self._notification_service.create_notification(
                body.assignee_id,
                tenant_id,
                "cr.assigned",
                "change_request",
                cr.id,
                f"You were assigned to CR: {cr.title}",
            )
        return await self._single(cr)

    async def list_crs(
        self,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        page: int,
        page_size: int,
        status_filter: CRStatus | None = None,
        author_id: uuid.UUID | None = None,
        assignee_id: uuid.UUID | None = None,
    ) -> CRListResponse:
        await self._project_service.get_project_or_404(tenant_id, project_id)
        items, total = await self._cr_repo.find_by_project_filtered(
            project_id,
            status=status_filter,
            author_id=author_id,
            assignee_id=assignee_id,
            page=page,
            page_size=page_size,
        )
        responses = await self._enrich([CRResponse.model_validate(i) for i in items], items)
        return CRListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total > 0 else 0,
        )

    async def get_cr(
        self, tenant_id: uuid.UUID, project_id: uuid.UUID, cr_id: uuid.UUID
    ) -> CRResponse:
        await self._project_service.get_project_or_404(tenant_id, project_id)
        cr = await self._get_cr_in_project_or_404(project_id, cr_id)
        return await self._single(cr)

    async def update_cr(
        self,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        cr_id: uuid.UUID,
        body: CRUpdate,
        actor_user_id: uuid.UUID,
    ) -> CRResponse:
        await self._project_service.get_project_or_404(tenant_id, project_id)
        cr = await self._get_cr_in_project_or_404(project_id, cr_id)

        updates: dict[Any, Any] = {}
        if body.title is not None:
            updates[ChangeRequest.title] = body.title
        if body.body is not None:
            updates[ChangeRequest.body] = body.body
        if body.target_files is not None:
            updates[ChangeRequest.target_files] = body.target_files
        if body.slug is not None:
            new_slug = slugify(body.slug)
            existing = await self._cr_repo.find_by_slug(project_id, new_slug)
            if existing is not None and existing.id != cr_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="Slug already in use"
                )
            updates[ChangeRequest.slug] = new_slug

        project = await self._project_service.get_project_or_404(tenant_id, project_id)

        # Detect real content changes (title/body) before applying updates:
        # no-op saves must not trigger content_changed notifications.
        changed_fields: list[str] = []
        if body.title is not None and body.title != cr.title:
            changed_fields.append("title")
        if body.body is not None and body.body != cr.body:
            changed_fields.append("body")

        if updates:
            await cr.set(updates)

        if changed_fields:
            await self._audit_service.log_event(
                tenant_id,
                actor_user_id,
                "cr.content_changed",
                "change_request",
                cr.id,
                entity_label=cr.title,
                summary=f"changed {', '.join(changed_fields)}",
                details={"changed_fields": changed_fields},
            )
            await self._collaboration_service.notify_content_changed(
                tenant_id,
                actor_user_id,
                EntityType.change_request.value,
                cr,
                changed_fields,
                project_name=project.name,
            )

        # Assignment changes are routed through the shared assignment flow
        # (validation, audit cr.assigned, notification, history) — PATCH keeps
        # supporting assignee_id for backwards compatibility; None means "not
        # provided" (use POST /assign to unassign).
        if body.assignee_id is not None:
            await self._assignment_service.apply_assignment(
                tenant_id, actor_user_id, cr, "change_request", body.assignee_id
            )

        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            "cr.updated",
            "change_request",
            cr.id,
            entity_label=cr.title,
            summary="updated",
        )
        reloaded = await self._cr_repo.find_by_id(cr_id)
        assert reloaded is not None, "change request vanished during update"
        return await self._single(reloaded)

    async def assign_cr(
        self,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        cr_id: uuid.UUID,
        new_assignee_id: uuid.UUID | None,
        actor_user_id: uuid.UUID,
    ) -> CRResponse:
        """Assign the CR to a tenant member (or unassign with assignee_id=null)."""
        await self._project_service.get_project_or_404(tenant_id, project_id)
        cr = await self._get_cr_in_project_or_404(project_id, cr_id)

        await self._assignment_service.apply_assignment(
            tenant_id, actor_user_id, cr, "change_request", new_assignee_id
        )

        reloaded = await self._cr_repo.find_by_id(cr_id)
        assert reloaded is not None, "change request vanished during assignment"
        return await self._single(reloaded)

    async def list_cr_assignments(
        self, tenant_id: uuid.UUID, project_id: uuid.UUID, cr_id: uuid.UUID
    ) -> list[AssignmentEntryResponse]:
        """Append-only assignment history for the CR (newest first)."""
        await self._project_service.get_project_or_404(tenant_id, project_id)
        await self._get_cr_in_project_or_404(project_id, cr_id)

        entries = await self._assignment_service.history_for("change_request", cr_id)
        user_ids: set[uuid.UUID] = set()
        for e in entries:
            if e.assignee_id is not None:
                user_ids.add(e.assignee_id)
            if e.assigned_by is not None:
                user_ids.add(e.assigned_by)
        users = await self._user_service.resolve_user_briefs(user_ids)

        return [
            AssignmentEntryResponse(
                id=e.id,
                assignee_id=e.assignee_id,
                assignee=users.get(e.assignee_id) if e.assignee_id is not None else None,
                assigned_by=e.assigned_by,
                assigned_by_name=(
                    users[e.assigned_by].display_name
                    if e.assigned_by is not None and e.assigned_by in users
                    else None
                ),
                created_at=e.created_at,
            )
            for e in entries
        ]

    async def transition_cr(
        self,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        cr_id: uuid.UUID,
        body: CRTransition,
        actor_user_id: uuid.UUID,
    ) -> CRResponse:
        await self._project_service.get_project_or_404(tenant_id, project_id)
        cr = await self._get_cr_in_project_or_404(project_id, cr_id)

        if cr.status in (CRStatus.deleted, CRStatus.closed):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot transition a {cr.status.value} item",
            )

        old_status = cr.status
        updates: dict[Any, Any] = {ChangeRequest.status: body.status}
        if body.status in (CRStatus.closed, CRStatus.applied, CRStatus.rejected):
            updates[ChangeRequest.closed_at] = datetime.now(UTC)
        await cr.set(updates)

        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            "cr.transitioned",
            "change_request",
            cr.id,
            entity_label=cr.title,
            summary=f"status: {old_status.value} → {body.status.value}",
            details={"old_status": old_status.value, "new_status": body.status.value},
        )

        if cr.author_id != actor_user_id:
            await self._notification_service.create_notification(
                cr.author_id,
                tenant_id,
                "cr.transitioned",
                "change_request",
                cr.id,
                f"CR '{cr.title}' moved to {body.status.value}",
            )
        reloaded = await self._cr_repo.find_by_id(cr_id)
        assert reloaded is not None, "change request vanished during transition"
        return await self._single(reloaded)

    # ── comments ──────────────────────────────────────────────────────────────

    async def list_cr_comments(
        self, tenant_id: uuid.UUID, project_id: uuid.UUID, cr_id: uuid.UUID
    ) -> list[CommentResponse]:
        await self._project_service.get_project_or_404(tenant_id, project_id)
        await self._get_cr_in_project_or_404(project_id, cr_id)

        comments = await self._comment_repo.find_by_entity(EntityType.change_request.value, cr_id)
        return await self._attach_comment_authors(comments)

    async def add_cr_comment(
        self,
        tenant_id: uuid.UUID,
        project_id: uuid.UUID,
        cr_id: uuid.UUID,
        body: CommentCreate,
        actor_user_id: uuid.UUID,
    ) -> CommentResponse:
        project = await self._project_service.get_project_or_404(tenant_id, project_id)
        cr = await self._get_cr_in_project_or_404(project_id, cr_id)

        comment = Comment(
            entity_type=EntityType.change_request,
            entity_id=cr_id,
            author_id=actor_user_id,
            body=body.body,
        )
        await self._comment_repo.create(comment)

        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            "cr.commented",
            "change_request",
            cr.id,
            entity_label=cr.title,
            summary="commented",
        )

        # Notify all actors (author, assignee, previous commenters except the
        # comment author) in-app, plus emails per preference. Best-effort.
        await self._collaboration_service.notify_comment_added(
            tenant_id,
            actor_user_id,
            EntityType.change_request.value,
            cr,
            comment,
            project_name=project.name,
        )
        return (await self._attach_comment_authors([comment]))[0]

    async def _attach_comment_authors(self, comments: list[Comment]) -> list[CommentResponse]:
        """Attach resolved author UserBrief to each comment (batch, no N+1)."""
        author_ids = {c.author_id for c in comments}
        users = await self._user_service.resolve_user_briefs(author_ids)
        responses = [CommentResponse.model_validate(c) for c in comments]
        for resp, c in zip(responses, comments):
            resp.author = users.get(c.author_id)
        return responses
