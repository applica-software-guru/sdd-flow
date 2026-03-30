import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth import get_current_tenant_member, require_role
from app.models.tenant_member import MemberRole, TenantMember
from app.repositories import ProjectRepository
from app.schemas.projects import ProjectCreate, ProjectResetRequest, ProjectResetResponse, ProjectResponse, ProjectStats, ProjectUpdate
from app.services.project_reset import reset_project_data
from app.services.audit import log_event

router = APIRouter(prefix="/tenants/{tenant_id}/projects", tags=["projects"])


def _project_response(project, stats_dict: dict) -> ProjectResponse:
    stats_data = stats_dict.get(project.id, {"doc_count": 0, "open_cr_count": 0, "open_bug_count": 0})
    stats = ProjectStats(
        document_count=stats_data["doc_count"],
        open_cr_count=stats_data["open_cr_count"],
        open_bug_count=stats_data["open_bug_count"],
    )
    resp = ProjectResponse.model_validate(project)
    resp.stats = stats
    return resp


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    tenant_id: uuid.UUID,
    body: ProjectCreate,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin, MemberRole.member)),
):
    project_repo = ProjectRepository()
    existing = await project_repo.find_by_slug(tenant_id, body.slug)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project slug already exists in this tenant")

    from app.models.project import Project
    project = Project(
        tenant_id=tenant_id, name=body.name, slug=body.slug, description=body.description
    )
    await project_repo.save(project)

    await log_event(tenant_id, member.user_id, "project.created", "project", project.id)

    stats_dict = await project_repo.get_stats_batch([project.id])
    return _project_response(project, stats_dict)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    tenant_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
):
    project_repo = ProjectRepository()
    projects = await project_repo.find_by_tenant(tenant_id)
    if not projects:
        return []
    project_ids = [p.id for p in projects]
    stats_dict = await project_repo.get_stats_batch(project_ids)
    return [_project_response(p, stats_dict) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
):
    project_repo = ProjectRepository()
    project = await project_repo.find_by_id(project_id)
    if project is None or str(project.tenant_id) != str(tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    stats_dict = await project_repo.get_stats_batch([project.id])
    return _project_response(project, stats_dict)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: ProjectUpdate,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin, MemberRole.member)),
):
    project_repo = ProjectRepository()
    project = await project_repo.find_by_id(project_id)
    if project is None or str(project.tenant_id) != str(tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    from app.models.project import Project
    updates = {}
    if body.name is not None:
        updates[Project.name] = body.name
    if body.description is not None:
        updates[Project.description] = body.description

    if updates:
        await project.set(updates)

    await log_event(tenant_id, member.user_id, "project.updated", "project", project.id)
    project = await project_repo.find_by_id(project_id)
    stats_dict = await project_repo.get_stats_batch([project.id])
    return _project_response(project, stats_dict)


@router.post("/{project_id}/archive", response_model=ProjectResponse)
async def archive_project(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin)),
):
    project_repo = ProjectRepository()
    project = await project_repo.find_by_id(project_id)
    if project is None or str(project.tenant_id) != str(tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    from app.models.project import Project
    await project.set({Project.archived_at: datetime.now(timezone.utc)})

    await log_event(tenant_id, member.user_id, "project.archived", "project", project.id)
    project = await project_repo.find_by_id(project_id)
    stats_dict = await project_repo.get_stats_batch([project.id])
    return _project_response(project, stats_dict)


@router.post("/{project_id}/restore", response_model=ProjectResponse)
async def restore_project(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin)),
):
    project_repo = ProjectRepository()
    project = await project_repo.find_by_id(project_id)
    if project is None or str(project.tenant_id) != str(tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    from app.models.project import Project
    await project.set({Project.archived_at: None})

    await log_event(tenant_id, member.user_id, "project.restored", "project", project.id)
    project = await project_repo.find_by_id(project_id)
    stats_dict = await project_repo.get_stats_batch([project.id])
    return _project_response(project, stats_dict)


@router.post("/{project_id}/reset", response_model=ProjectResetResponse)
async def reset_project(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: ProjectResetRequest,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin)),
):
    project_repo = ProjectRepository()
    project = await project_repo.find_by_id(project_id)
    if project is None or str(project.tenant_id) != str(tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if body.confirm_slug != project.slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Slug mismatch: expected '{project.slug}'",
        )

    counts = await reset_project_data(project, tenant_id, member.user_id)
    return ProjectResetResponse(
        message=f"Project '{project.name}' has been reset",
        **counts,
    )
