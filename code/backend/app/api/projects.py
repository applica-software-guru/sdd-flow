import uuid

from fastapi import APIRouter, Depends, status

from app.dependencies import get_project_service
from app.middleware.auth import get_current_tenant_member, require_role
from app.models.tenant_member import MemberRole, TenantMember
from app.schemas.projects import (
    ProjectCreate,
    ProjectResetRequest,
    ProjectResetResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.projects import ProjectService

router = APIRouter(prefix="/tenants/{tenant_id}/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    tenant_id: uuid.UUID,
    body: ProjectCreate,
    member: TenantMember = Depends(
        require_role(MemberRole.owner, MemberRole.admin, MemberRole.member)
    ),
    svc: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    return await svc.create_project(tenant_id, body, member.user_id)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    tenant_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: ProjectService = Depends(get_project_service),
) -> list[ProjectResponse]:
    return await svc.list_projects(tenant_id)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    return await svc.get_project(tenant_id, project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: ProjectUpdate,
    member: TenantMember = Depends(
        require_role(MemberRole.owner, MemberRole.admin, MemberRole.member)
    ),
    svc: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    return await svc.update_project(tenant_id, project_id, body, member.user_id)


@router.post("/{project_id}/archive", response_model=ProjectResponse)
async def archive_project(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin)),
    svc: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    return await svc.archive_project(tenant_id, project_id, member.user_id)


@router.post("/{project_id}/restore", response_model=ProjectResponse)
async def restore_project(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin)),
    svc: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    return await svc.restore_project(tenant_id, project_id, member.user_id)


@router.post("/{project_id}/reset", response_model=ProjectResetResponse)
async def reset_project(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: ProjectResetRequest,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin)),
    svc: ProjectService = Depends(get_project_service),
) -> ProjectResetResponse:
    return await svc.reset_project(tenant_id, project_id, body.confirm_slug, member.user_id)
