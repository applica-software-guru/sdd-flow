import uuid

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_bug_service
from app.middleware.auth import get_current_tenant_member
from app.models.bug import BugSeverity, BugStatus
from app.models.tenant_member import TenantMember
from app.schemas.bugs import (
    AssignBug,
    AssignmentEntryResponse,
    BugCreate,
    BugListResponse,
    BugResponse,
    BugTransition,
    BugUpdate,
)
from app.schemas.comments import CommentCreate, CommentResponse
from app.services.bugs import BugService

router = APIRouter(
    prefix="/tenants/{tenant_id}/projects/{project_id}/bugs",
    tags=["bugs"],
)


@router.post("", response_model=BugResponse, status_code=status.HTTP_201_CREATED)
async def create_bug(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: BugCreate,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: BugService = Depends(get_bug_service),
) -> BugResponse:
    return await svc.create_bug(tenant_id, project_id, body, member.user_id)


@router.get("", response_model=BugListResponse)
async def list_bugs(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: BugStatus | None = Query(None, alias="status"),
    severity_filter: BugSeverity | None = Query(None, alias="severity"),
    author_id: uuid.UUID | None = Query(None),
    assignee_id: uuid.UUID | None = Query(None),
    member: TenantMember = Depends(get_current_tenant_member),
    svc: BugService = Depends(get_bug_service),
) -> BugListResponse:
    return await svc.list_bugs(
        tenant_id,
        project_id,
        page,
        page_size,
        status_filter=status_filter,
        severity_filter=severity_filter,
        author_id=author_id,
        assignee_id=assignee_id,
    )


@router.get("/{bug_id}", response_model=BugResponse)
async def get_bug(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: BugService = Depends(get_bug_service),
) -> BugResponse:
    return await svc.get_bug(tenant_id, project_id, bug_id)


@router.patch("/{bug_id}", response_model=BugResponse)
async def update_bug(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    body: BugUpdate,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: BugService = Depends(get_bug_service),
) -> BugResponse:
    return await svc.update_bug(tenant_id, project_id, bug_id, body, member.user_id)


@router.post("/{bug_id}/assign", response_model=BugResponse)
async def assign_bug(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    body: AssignBug,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: BugService = Depends(get_bug_service),
) -> BugResponse:
    """Assign the bug to a tenant member (or unassign with assignee_id=null)."""
    return await svc.assign_bug(tenant_id, project_id, bug_id, body.assignee_id, member.user_id)


@router.get("/{bug_id}/assignments", response_model=list[AssignmentEntryResponse])
async def list_bug_assignments(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: BugService = Depends(get_bug_service),
) -> list[AssignmentEntryResponse]:
    """Append-only assignment history for the bug (newest first)."""
    return await svc.list_bug_assignments(tenant_id, project_id, bug_id)


@router.post("/{bug_id}/transition", response_model=BugResponse)
async def transition_bug(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    body: BugTransition,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: BugService = Depends(get_bug_service),
) -> BugResponse:
    return await svc.transition_bug(tenant_id, project_id, bug_id, body, member.user_id)


@router.get("/{bug_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: BugService = Depends(get_bug_service),
) -> list[CommentResponse]:
    return await svc.list_bug_comments(tenant_id, project_id, bug_id)


@router.post(
    "/{bug_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED
)
async def add_comment(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    body: CommentCreate,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: BugService = Depends(get_bug_service),
) -> CommentResponse:
    return await svc.add_bug_comment(tenant_id, project_id, bug_id, body, member.user_id)
