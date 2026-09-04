"""Project reset service: full data wipe for a project (cascading deletes)."""

import uuid
from typing import Any

from app.models.project import Project
from app.repositories import (
    AuditRepository,
    BugRepository,
    ChangeRequestRepository,
    CommentRepository,
    DocumentFileRepository,
    NotificationRepository,
    WorkerRepository,
)
from app.services.audit import AuditService


class ProjectResetService:
    def __init__(
        self,
        cr_repo: ChangeRequestRepository,
        bug_repo: BugRepository,
        doc_repo: DocumentFileRepository,
        comment_repo: CommentRepository,
        notification_repo: NotificationRepository,
        audit_repo: AuditRepository,
        worker_repo: WorkerRepository,
        audit_service: AuditService,
    ) -> None:
        self._cr_repo = cr_repo
        self._bug_repo = bug_repo
        self._doc_repo = doc_repo
        self._comment_repo = comment_repo
        self._notification_repo = notification_repo
        self._audit_repo = audit_repo
        self._worker_repo = worker_repo
        self._audit_service = audit_service

    async def reset_project_data(
        self,
        project: Project,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID | None,
    ) -> dict[str, Any]:
        """Delete all documents, CRs, bugs, workers, jobs, and related data for a project."""
        # 1. Collect IDs for comment / notification deletion
        crs = await self._cr_repo.find_by_project(project.id, page=1, page_size=100_000)
        cr_list = crs[0]
        bugs = await self._bug_repo.find_by_project(project.id, page=1, page_size=100_000)
        bug_list = bugs[0]
        docs = await self._doc_repo.find_by_project(project.id)

        cr_ids = [cr.id for cr in cr_list]
        bug_ids = [b.id for b in bug_list]
        doc_ids = [d.id for d in docs]

        # 2. Workers / jobs / messages (full cascade)
        worker_counts = await self._worker_repo.delete_by_project(project.id)
        deleted_workers = worker_counts.get("workers", 0)
        deleted_jobs = worker_counts.get("jobs", 0)
        deleted_messages = worker_counts.get("messages", 0)

        # 3. Comments on CRs and bugs
        deleted_comments = await self._comment_repo.delete_by_project_entities(cr_ids, bug_ids)

        # 4. Notifications for project entities (CRs, bugs, docs)
        all_entity_uuids = cr_ids + bug_ids + doc_ids
        deleted_notifications = 0
        if all_entity_uuids:
            deleted_notifications = await self._notification_repo.delete_by_entity_ids(
                tenant_id, all_entity_uuids
            )

        # 5. Delete core project content
        deleted_bugs = await self._bug_repo.delete_by_project(project.id)
        deleted_crs = await self._cr_repo.delete_by_project(project.id)
        deleted_docs = await self._doc_repo.delete_by_project(project.id)

        # 6. Audit trail (label captured before deletion, entities no longer exist)
        await self._audit_service.log_event(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="project.reset",
            entity_type="project",
            entity_id=project.id,
            entity_label=project.name,
            summary=(
                f"reset: {deleted_bugs} bugs, {deleted_crs} change requests, "
                f"{deleted_docs} documents deleted"
            ),
            details={
                "deleted_documents": deleted_docs,
                "deleted_change_requests": deleted_crs,
                "deleted_bugs": deleted_bugs,
                "deleted_comments": deleted_comments,
                "deleted_notifications": deleted_notifications,
                "deleted_workers": deleted_workers,
                "deleted_jobs": deleted_jobs,
                "deleted_messages": deleted_messages,
            },
        )

        return {
            "deleted_documents": deleted_docs,
            "deleted_change_requests": deleted_crs,
            "deleted_bugs": deleted_bugs,
            "deleted_comments": deleted_comments,
            "deleted_notifications": deleted_notifications,
            "deleted_workers": deleted_workers,
            "deleted_jobs": deleted_jobs,
            "deleted_messages": deleted_messages,
        }
