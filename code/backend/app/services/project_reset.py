import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bug import Bug
from app.models.change_request import ChangeRequest
from app.models.comment import Comment
from app.models.document_file import DocumentFile
from app.models.notification import Notification
from app.models.project import Project
from app.services.audit import log_event


async def reset_project_data(
    db: AsyncSession,
    project: Project,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None,
) -> dict:
    """Delete all documents, CRs, bugs, and related comments/notifications for a project."""

    # Collect entity IDs via subqueries (avoids materialising large lists in Python)
    cr_ids_sq = select(ChangeRequest.id).where(ChangeRequest.project_id == project.id)
    bug_ids_sq = select(Bug.id).where(Bug.project_id == project.id)
    doc_ids_sq = select(DocumentFile.id).where(DocumentFile.project_id == project.id)

    # 1. Delete orphan-prone entities first
    comments_result = await db.execute(
        delete(Comment).where(
            (Comment.entity_id.in_(cr_ids_sq)) | (Comment.entity_id.in_(bug_ids_sq))
        )
    )
    deleted_comments = comments_result.rowcount

    notifications_result = await db.execute(
        delete(Notification).where(
            Notification.tenant_id == tenant_id,
            (
                Notification.entity_id.in_(cr_ids_sq)
                | Notification.entity_id.in_(bug_ids_sq)
                | Notification.entity_id.in_(doc_ids_sq)
            ),
        )
    )
    deleted_notifications = notifications_result.rowcount

    # 2. Delete project content
    bugs_result = await db.execute(
        delete(Bug).where(Bug.project_id == project.id)
    )
    deleted_bugs = bugs_result.rowcount

    crs_result = await db.execute(
        delete(ChangeRequest).where(ChangeRequest.project_id == project.id)
    )
    deleted_crs = crs_result.rowcount

    docs_result = await db.execute(
        delete(DocumentFile).where(DocumentFile.project_id == project.id)
    )
    deleted_docs = docs_result.rowcount

    # 3. Audit trail
    await log_event(
        db,
        tenant_id,
        user_id,
        "project.reset",
        "project",
        project.id,
        details={
            "deleted_documents": deleted_docs,
            "deleted_change_requests": deleted_crs,
            "deleted_bugs": deleted_bugs,
            "deleted_comments": deleted_comments,
            "deleted_notifications": deleted_notifications,
        },
    )

    return {
        "deleted_documents": deleted_docs,
        "deleted_change_requests": deleted_crs,
        "deleted_bugs": deleted_bugs,
        "deleted_comments": deleted_comments,
        "deleted_notifications": deleted_notifications,
    }
