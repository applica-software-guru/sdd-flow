import uuid

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_change_request_service
from app.middleware.auth import get_current_tenant_member
from app.models.change_request import CRStatus
from app.models.tenant_member import TenantMember
from app.schemas.change_requests import (
    AssignCR,
    AssignmentEntryResponse,
    CRCreate,
    CRListResponse,
    CRResponse,
    CRTransition,
    CRUpdate,
)
from app.schemas.comments import CommentCreate, CommentResponse
from app.services.change_requests import ChangeRequestService

router = APIRouter(
    prefix="/tenants/{tenant_id}/projects/{project_id}/change-requests",
    tags=["change_requests"],
)


@router.post("", response_model=CRResponse, status_code=status.HTTP_201_CREATED)
async def create_cr(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: CRCreate,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: ChangeRequestService = Depends(get_change_request_service),
) -> CRResponse:
    return await svc.create_cr(tenant_id, project_id, body, member.user_id)


@router.get("", response_model=CRListResponse)
async def list_crs(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: CRStatus | None = Query(None, alias="status"),
    author_id: uuid.UUID | None = Query(None),
    assignee_id: uuid.UUID | None = Query(None),
    member: TenantMember = Depends(get_current_tenant_member),
    svc: ChangeRequestService = Depends(get_change_request_service),
) -> CRListResponse:
    return await svc.list_crs(
        tenant_id,
        project_id,
        page,
        page_size,
        status_filter=status_filter,
        author_id=author_id,
        assignee_id=assignee_id,
    )


@router.get("/{cr_id}", response_model=CRResponse)
async def get_cr(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: ChangeRequestService = Depends(get_change_request_service),
) -> CRResponse:
    return await svc.get_cr(tenant_id, project_id, cr_id)


@router.patch("/{cr_id}", response_model=CRResponse)
async def update_cr(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    body: CRUpdate,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: ChangeRequestService = Depends(get_change_request_service),
) -> CRResponse:
    return await svc.update_cr(tenant_id, project_id, cr_id, body, member.user_id)


@router.post("/{cr_id}/assign", response_model=CRResponse)
async def assign_cr(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    body: AssignCR,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: ChangeRequestService = Depends(get_change_request_service),
) -> CRResponse:
    """Assign the CR to a tenant member (or unassign with assignee_id=null)."""
    return await svc.assign_cr(tenant_id, project_id, cr_id, body.assignee_id, member.user_id)


@router.get("/{cr_id}/assignments", response_model=list[AssignmentEntryResponse])
async def list_cr_assignments(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: ChangeRequestService = Depends(get_change_request_service),
) -> list[AssignmentEntryResponse]:
    """Append-only assignment history for the CR (newest first)."""
    return await svc.list_cr_assignments(tenant_id, project_id, cr_id)


@router.post("/{cr_id}/transition", response_model=CRResponse)
async def transition_cr(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    body: CRTransition,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: ChangeRequestService = Depends(get_change_request_service),
) -> CRResponse:
    return await svc.transition_cr(tenant_id, project_id, cr_id, body, member.user_id)


@router.get("/{cr_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: ChangeRequestService = Depends(get_change_request_service),
) -> list[CommentResponse]:
    return await svc.list_cr_comments(tenant_id, project_id, cr_id)


@router.post(
    "/{cr_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED
)
async def add_comment(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    body: CommentCreate,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: ChangeRequestService = Depends(get_change_request_service),
) -> CommentResponse:
    return await svc.add_cr_comment(tenant_id, project_id, cr_id, body, member.user_id)
