import uuid

from app.models.project import Project
from app.repositories import (
    ChangeRequestRepository,
    BugRepository,
    DocumentFileRepository,
    CommentRepository,
    NotificationRepository,
    AuditRepository,
    WorkerRepository,
)
from app.services.audit import log_event


async def reset_project_data(
    project: Project,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None,
    cr_repo: ChangeRequestRepository = None,
    bug_repo: BugRepository = None,
    doc_repo: DocumentFileRepository = None,
    comment_repo: CommentRepository = None,
    notification_repo: NotificationRepository = None,
    audit_repo: AuditRepository = None,
    worker_repo: WorkerRepository = None,
) -> dict:
    """Delete all documents, CRs, bugs, workers, jobs, and related data for a project."""
    if cr_repo is None:
        cr_repo = ChangeRequestRepository()
    if bug_repo is None:
        bug_repo = BugRepository()
    if doc_repo is None:
        doc_repo = DocumentFileRepository()
    if comment_repo is None:
        comment_repo = CommentRepository()
    if notification_repo is None:
        notification_repo = NotificationRepository()
    if audit_repo is None:
        audit_repo = AuditRepository()
    if worker_repo is None:
        worker_repo = WorkerRepository()

    # 1. Collect IDs for comment / notification deletion
    crs = await cr_repo.find_by_project(project.id, page=1, page_size=100_000)
    cr_list = crs[0]
    bugs = await bug_repo.find_by_project(project.id, page=1, page_size=100_000)
    bug_list = bugs[0]
    docs = await doc_repo.find_by_project(project.id)

    cr_ids = [cr.id for cr in cr_list]
    bug_ids = [b.id for b in bug_list]
    doc_ids = [d.id for d in docs]

    # 2. Workers / jobs / messages (full cascade)
    worker_counts = await worker_repo.delete_by_project(project.id)
    deleted_workers = worker_counts.get("workers", 0)
    deleted_jobs = worker_counts.get("jobs", 0)
    deleted_messages = worker_counts.get("messages", 0)

    # 3. Comments on CRs and bugs
    deleted_comments = await comment_repo.delete_by_project_entities(cr_ids, bug_ids)

    # 4. Notifications for project entities (CRs, bugs, docs)
    all_entity_uuids = cr_ids + bug_ids + doc_ids
    deleted_notifications = 0
    if all_entity_uuids:
        from app.models.notification import Notification
        from bson.binary import Binary, UuidRepresentation
        entity_bins = [Binary.from_uuid(i, uuid_representation=UuidRepresentation.STANDARD) for i in all_entity_uuids]
        result = await Notification.find(
            {"tenantId": tenant_id, "entityId": {"$in": entity_bins}}
        ).delete()
        deleted_notifications = result.deleted_count if result else 0

    # 5. Delete core project content
    deleted_bugs = await bug_repo.delete_by_project(project.id)
    deleted_crs = await cr_repo.delete_by_project(project.id)
    deleted_docs = await doc_repo.delete_by_project(project.id)

    # 6. Audit trail
    await log_event(
        tenant_id=tenant_id,
        user_id=user_id,
        event_type="project.reset",
        entity_type="project",
        entity_id=project.id,
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
        audit_repo=audit_repo,
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
