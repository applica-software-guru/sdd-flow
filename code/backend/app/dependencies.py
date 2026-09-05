"""Composition root: the single place where repositories and services are wired.

Controllers receive fully-constructed service classes via ``Depends(...)``;
no other module may instantiate a repository or a service. Tests substitute
any component with ``app.dependency_overrides[get_bug_service] = lambda: fake``.
"""

from fastapi import Depends

from app.repositories import (
    ApiKeyRepository,
    AssignmentRepository,
    AuditRepository,
    AuthRepository,
    BugRepository,
    ChangeRequestRepository,
    CommentRepository,
    DocumentFileRepository,
    NotificationRepository,
    PlatformAdminRepository,
    ProjectRepository,
    TenantRepository,
    UserRepository,
    WorkerRepository,
)
from app.services.api_keys import ApiKeyService
from app.services.assignment import AssignmentService
from app.services.audit import AuditService
from app.services.auth import AuthService
from app.services.bugs import BugService
from app.services.change_requests import ChangeRequestService
from app.services.collab_notifications import CollaborationService
from app.services.documents import DocumentService
from app.services.notifications import NotificationService
from app.services.numbering import NumberingService
from app.services.platform_admin import PlatformAdminService
from app.services.project_reset import ProjectResetService
from app.services.projects import ProjectService
from app.services.search import SearchService
from app.services.sync import SyncService
from app.services.tenant_dashboard import TenantDashboardService
from app.services.tenants import TenantService
from app.services.users import UserService
from app.services.worker_jobs import WorkerJobService

# ── repository providers ──────────────────────────────────────────────────────


def get_user_repository() -> UserRepository:
    return UserRepository()


def get_tenant_repository() -> TenantRepository:
    return TenantRepository()


def get_project_repository() -> ProjectRepository:
    return ProjectRepository()


def get_document_file_repository() -> DocumentFileRepository:
    return DocumentFileRepository()


def get_change_request_repository() -> ChangeRequestRepository:
    return ChangeRequestRepository()


def get_bug_repository() -> BugRepository:
    return BugRepository()


def get_comment_repository() -> CommentRepository:
    return CommentRepository()


def get_audit_repository() -> AuditRepository:
    return AuditRepository()


def get_assignment_repository() -> AssignmentRepository:
    return AssignmentRepository()


def get_notification_repository() -> NotificationRepository:
    return NotificationRepository()


def get_auth_repository() -> AuthRepository:
    return AuthRepository()


def get_platform_admin_repository() -> PlatformAdminRepository:
    return PlatformAdminRepository()


def get_worker_repository() -> WorkerRepository:
    return WorkerRepository()


def get_api_key_repository() -> ApiKeyRepository:
    return ApiKeyRepository()


# ── collaborator services ─────────────────────────────────────────────────────


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
) -> UserService:
    return UserService(user_repo=user_repo, tenant_repo=tenant_repo)


def get_audit_service(
    audit_repo: AuditRepository = Depends(get_audit_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
) -> AuditService:
    return AuditService(audit_repo=audit_repo, user_repo=user_repo, tenant_repo=tenant_repo)


def get_notification_service(
    notification_repo: NotificationRepository = Depends(get_notification_repository),
) -> NotificationService:
    return NotificationService(notification_repo)


def get_platform_admin_service(
    repository: PlatformAdminRepository = Depends(get_platform_admin_repository),
    audit_service: AuditService = Depends(get_audit_service),
) -> PlatformAdminService:
    return PlatformAdminService(repository=repository, audit_service=audit_service)


def get_assignment_service(
    assignment_repo: AssignmentRepository = Depends(get_assignment_repository),
    audit_service: AuditService = Depends(get_audit_service),
    notification_service: NotificationService = Depends(get_notification_service),
    user_service: UserService = Depends(get_user_service),
) -> AssignmentService:
    return AssignmentService(
        assignment_repo=assignment_repo,
        audit_service=audit_service,
        notification_service=notification_service,
        user_service=user_service,
    )


def get_collaboration_service(
    notification_service: NotificationService = Depends(get_notification_service),
    notification_repo: NotificationRepository = Depends(get_notification_repository),
    comment_repo: CommentRepository = Depends(get_comment_repository),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    user_repo: UserRepository = Depends(get_user_repository),
) -> CollaborationService:
    return CollaborationService(
        notification_service=notification_service,
        notification_repo=notification_repo,
        comment_repo=comment_repo,
        tenant_repo=tenant_repo,
        user_repo=user_repo,
    )


def get_numbering_service(
    bug_repo: BugRepository = Depends(get_bug_repository),
    cr_repo: ChangeRequestRepository = Depends(get_change_request_repository),
) -> NumberingService:
    return NumberingService(bug_repo=bug_repo, cr_repo=cr_repo)


def get_project_reset_service(
    cr_repo: ChangeRequestRepository = Depends(get_change_request_repository),
    bug_repo: BugRepository = Depends(get_bug_repository),
    doc_repo: DocumentFileRepository = Depends(get_document_file_repository),
    comment_repo: CommentRepository = Depends(get_comment_repository),
    notification_repo: NotificationRepository = Depends(get_notification_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
    worker_repo: WorkerRepository = Depends(get_worker_repository),
    audit_service: AuditService = Depends(get_audit_service),
) -> ProjectResetService:
    return ProjectResetService(
        cr_repo=cr_repo,
        bug_repo=bug_repo,
        doc_repo=doc_repo,
        comment_repo=comment_repo,
        notification_repo=notification_repo,
        audit_repo=audit_repo,
        worker_repo=worker_repo,
        audit_service=audit_service,
    )


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    auth_repo: AuthRepository = Depends(get_auth_repository),
) -> AuthService:
    return AuthService(user_repo=user_repo, auth_repo=auth_repo)


# ── domain services ───────────────────────────────────────────────────────────


def get_project_service(
    project_repo: ProjectRepository = Depends(get_project_repository),
    audit_service: AuditService = Depends(get_audit_service),
    reset_service: ProjectResetService = Depends(get_project_reset_service),
) -> ProjectService:
    return ProjectService(
        project_repo=project_repo,
        audit_service=audit_service,
        reset_service=reset_service,
    )


def get_api_key_service(
    project_service: ProjectService = Depends(get_project_service),
    api_key_repo: ApiKeyRepository = Depends(get_api_key_repository),
    audit_service: AuditService = Depends(get_audit_service),
) -> ApiKeyService:
    return ApiKeyService(
        project_service=project_service,
        api_key_repo=api_key_repo,
        audit_service=audit_service,
    )


def get_bug_service(
    project_service: ProjectService = Depends(get_project_service),
    bug_repo: BugRepository = Depends(get_bug_repository),
    comment_repo: CommentRepository = Depends(get_comment_repository),
    user_service: UserService = Depends(get_user_service),
    audit_service: AuditService = Depends(get_audit_service),
    notification_service: NotificationService = Depends(get_notification_service),
    assignment_service: AssignmentService = Depends(get_assignment_service),
    collaboration_service: CollaborationService = Depends(get_collaboration_service),
    numbering_service: NumberingService = Depends(get_numbering_service),
) -> BugService:
    return BugService(
        project_service=project_service,
        bug_repo=bug_repo,
        comment_repo=comment_repo,
        user_service=user_service,
        audit_service=audit_service,
        notification_service=notification_service,
        assignment_service=assignment_service,
        collaboration_service=collaboration_service,
        numbering_service=numbering_service,
    )


def get_change_request_service(
    project_service: ProjectService = Depends(get_project_service),
    cr_repo: ChangeRequestRepository = Depends(get_change_request_repository),
    comment_repo: CommentRepository = Depends(get_comment_repository),
    user_service: UserService = Depends(get_user_service),
    audit_service: AuditService = Depends(get_audit_service),
    notification_service: NotificationService = Depends(get_notification_service),
    assignment_service: AssignmentService = Depends(get_assignment_service),
    collaboration_service: CollaborationService = Depends(get_collaboration_service),
    numbering_service: NumberingService = Depends(get_numbering_service),
) -> ChangeRequestService:
    return ChangeRequestService(
        project_service=project_service,
        cr_repo=cr_repo,
        comment_repo=comment_repo,
        user_service=user_service,
        audit_service=audit_service,
        notification_service=notification_service,
        assignment_service=assignment_service,
        collaboration_service=collaboration_service,
        numbering_service=numbering_service,
    )


def get_tenant_service(
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_service: AuditService = Depends(get_audit_service),
    project_repo: ProjectRepository = Depends(get_project_repository),
) -> TenantService:
    return TenantService(
        tenant_repo=tenant_repo,
        user_repo=user_repo,
        audit_service=audit_service,
        project_repo=project_repo,
    )


def get_tenant_dashboard_service(
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    project_repo: ProjectRepository = Depends(get_project_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
) -> TenantDashboardService:
    return TenantDashboardService(
        tenant_repo=tenant_repo,
        project_repo=project_repo,
        audit_repo=audit_repo,
    )


def get_document_service(
    project_service: ProjectService = Depends(get_project_service),
    doc_repo: DocumentFileRepository = Depends(get_document_file_repository),
    audit_service: AuditService = Depends(get_audit_service),
) -> DocumentService:
    return DocumentService(
        project_service=project_service,
        doc_repo=doc_repo,
        audit_service=audit_service,
    )


def get_worker_job_service(
    project_service: ProjectService = Depends(get_project_service),
    worker_repo: WorkerRepository = Depends(get_worker_repository),
    cr_repo: ChangeRequestRepository = Depends(get_change_request_repository),
    bug_repo: BugRepository = Depends(get_bug_repository),
    doc_repo: DocumentFileRepository = Depends(get_document_file_repository),
    comment_repo: CommentRepository = Depends(get_comment_repository),
    notification_service: NotificationService = Depends(get_notification_service),
) -> WorkerJobService:
    return WorkerJobService(
        project_service=project_service,
        worker_repo=worker_repo,
        cr_repo=cr_repo,
        bug_repo=bug_repo,
        doc_repo=doc_repo,
        comment_repo=comment_repo,
        notification_service=notification_service,
    )


def get_search_service(
    project_repo: ProjectRepository = Depends(get_project_repository),
    doc_repo: DocumentFileRepository = Depends(get_document_file_repository),
    cr_repo: ChangeRequestRepository = Depends(get_change_request_repository),
    bug_repo: BugRepository = Depends(get_bug_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
) -> SearchService:
    return SearchService(
        project_repo=project_repo,
        doc_repo=doc_repo,
        cr_repo=cr_repo,
        bug_repo=bug_repo,
        audit_repo=audit_repo,
    )


def get_sync_service(
    cr_repo: ChangeRequestRepository = Depends(get_change_request_repository),
    bug_repo: BugRepository = Depends(get_bug_repository),
    doc_repo: DocumentFileRepository = Depends(get_document_file_repository),
    numbering_service: NumberingService = Depends(get_numbering_service),
    reset_service: ProjectResetService = Depends(get_project_reset_service),
) -> SyncService:
    return SyncService(
        cr_repo=cr_repo,
        bug_repo=bug_repo,
        doc_repo=doc_repo,
        numbering_service=numbering_service,
        reset_service=reset_service,
    )
