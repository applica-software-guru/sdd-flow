import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_tenant_member, require_role
from app.models.bug import Bug, BugStatus
from app.models.change_request import CRStatus, ChangeRequest
from app.models.document_file import DocumentFile
from app.models.project import Project
from app.models.tenant_member import MemberRole, TenantMember
from app.schemas.projects import ProjectCreate, ProjectResponse, ProjectStats, ProjectUpdate
from app.services.audit import log_event

router = APIRouter(prefix="/tenants/{tenant_id}/projects", tags=["projects"])


async def _project_response(db: AsyncSession, project: Project) -> ProjectResponse:
    doc_count = await db.execute(
        select(func.count()).select_from(DocumentFile).where(DocumentFile.project_id == project.id)
    )
    cr_count = await db.execute(
        select(func.count())
        .select_from(ChangeRequest)
        .where(
            ChangeRequest.project_id == project.id,
            ChangeRequest.status.in_([CRStatus.draft, CRStatus.approved]),
        )
    )
    bug_count = await db.execute(
        select(func.count())
        .select_from(Bug)
        .where(
            Bug.project_id == project.id,
            Bug.status.in_([BugStatus.open, BugStatus.in_progress]),
        )
    )
    stats = ProjectStats(
        document_count=doc_count.scalar() or 0,
        open_cr_count=cr_count.scalar() or 0,
        open_bug_count=bug_count.scalar() or 0,
    )
    resp = ProjectResponse.model_validate(project)
    resp.stats = stats
    return resp


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    tenant_id: uuid.UUID,
    body: ProjectCreate,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin, MemberRole.member)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(Project.tenant_id == tenant_id, Project.slug == body.slug)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project slug already exists in this tenant")

    project = Project(
        tenant_id=tenant_id, name=body.name, slug=body.slug, description=body.description
    )
    db.add(project)
    await db.flush()

    await log_event(db, tenant_id, member.user_id, "project.created", "project", project.id)
    await db.refresh(project)
    return await _project_response(db, project)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    tenant_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(Project.tenant_id == tenant_id, Project.archived_at.is_(None))
    )
    projects = result.scalars().all()
    return [await _project_response(db, p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.tenant_id == tenant_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return await _project_response(db, project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: ProjectUpdate,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin, MemberRole.member)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.tenant_id == tenant_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if body.name is not None:
        project.name = body.name
    if body.description is not None:
        project.description = body.description
    await db.flush()

    await log_event(db, tenant_id, member.user_id, "project.updated", "project", project.id)
    await db.refresh(project)
    return await _project_response(db, project)


@router.post("/{project_id}/archive", response_model=ProjectResponse)
async def archive_project(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.tenant_id == tenant_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    project.archived_at = datetime.now(timezone.utc)
    await db.flush()

    await log_event(db, tenant_id, member.user_id, "project.archived", "project", project.id)
    await db.refresh(project)
    return await _project_response(db, project)


@router.post("/{project_id}/restore", response_model=ProjectResponse)
async def restore_project(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.tenant_id == tenant_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    project.archived_at = None
    await db.flush()

    await log_event(db, tenant_id, member.user_id, "project.restored", "project", project.id)
    await db.refresh(project)
    return await _project_response(db, project)
