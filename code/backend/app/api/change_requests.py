import math
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_tenant_member, get_current_user
from app.models.change_request import CRStatus, ChangeRequest
from app.models.comment import Comment, EntityType
from app.models.project import Project
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.schemas.change_requests import CRCreate, CRListResponse, CRResponse, CRTransition, CRUpdate
from app.schemas.comments import CommentCreate, CommentResponse
from app.services.audit import log_event
from app.services.notifications import create_notification
from app.services.slug import assign_number_and_slug

router = APIRouter(
    prefix="/tenants/{tenant_id}/projects/{project_id}/change-requests",
    tags=["change_requests"],
)


async def _get_project(db: AsyncSession, tenant_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.tenant_id == tenant_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("", response_model=CRResponse, status_code=status.HTTP_201_CREATED)
async def create_cr(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: CRCreate,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    number, slug = await assign_number_and_slug(db, ChangeRequest, project_id, body.title)
    cr = ChangeRequest(
        project_id=project_id,
        number=number,
        slug=slug,
        title=body.title,
        body=body.body,
        author_id=member.user_id,
        assignee_id=body.assignee_id,
        target_files=body.target_files,
    )
    db.add(cr)
    await db.flush()

    await log_event(db, tenant_id, member.user_id, "cr.created", "change_request", cr.id)

    if body.assignee_id and body.assignee_id != member.user_id:
        await create_notification(
            db, body.assignee_id, tenant_id, "cr.assigned",
            "change_request", cr.id, f"You were assigned to CR: {cr.title}",
        )
    await db.refresh(cr)
    return cr


@router.get("", response_model=CRListResponse)
async def list_crs(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: CRStatus | None = Query(None, alias="status"),
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    query = select(ChangeRequest).where(ChangeRequest.project_id == project_id)
    count_query = select(func.count()).select_from(ChangeRequest).where(ChangeRequest.project_id == project_id)

    if status_filter is not None:
        query = query.where(ChangeRequest.status == status_filter)
        count_query = count_query.where(ChangeRequest.status == status_filter)
    else:
        query = query.where(ChangeRequest.status != CRStatus.deleted)
        count_query = count_query.where(ChangeRequest.status != CRStatus.deleted)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(ChangeRequest.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return CRListResponse(
        items=[CRResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/{cr_id}", response_model=CRResponse)
async def get_cr(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    result = await db.execute(
        select(ChangeRequest).where(ChangeRequest.id == cr_id, ChangeRequest.project_id == project_id)
    )
    cr = result.scalar_one_or_none()
    if cr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")
    return cr


@router.patch("/{cr_id}", response_model=CRResponse)
async def update_cr(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    body: CRUpdate,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    result = await db.execute(
        select(ChangeRequest).where(ChangeRequest.id == cr_id, ChangeRequest.project_id == project_id)
    )
    cr = result.scalar_one_or_none()
    if cr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")

    if body.title is not None:
        cr.title = body.title
    if body.body is not None:
        cr.body = body.body
    if body.assignee_id is not None:
        cr.assignee_id = body.assignee_id
    if body.target_files is not None:
        cr.target_files = body.target_files
    await db.flush()

    await log_event(db, tenant_id, member.user_id, "cr.updated", "change_request", cr.id)
    await db.refresh(cr)
    return cr


@router.post("/{cr_id}/transition", response_model=CRResponse)
async def transition_cr(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    body: CRTransition,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    result = await db.execute(
        select(ChangeRequest).where(ChangeRequest.id == cr_id, ChangeRequest.project_id == project_id)
    )
    cr = result.scalar_one_or_none()
    if cr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")

    cr.status = body.status
    if body.status in (CRStatus.closed, CRStatus.applied, CRStatus.rejected):
        cr.closed_at = datetime.now(timezone.utc)
    await db.flush()

    await log_event(
        db, tenant_id, member.user_id, "cr.transitioned", "change_request", cr.id,
        details={"new_status": body.status.value},
    )

    if cr.author_id != member.user_id:
        await create_notification(
            db, cr.author_id, tenant_id, "cr.transitioned",
            "change_request", cr.id, f"CR '{cr.title}' moved to {body.status.value}",
        )
    await db.refresh(cr)
    return cr


@router.get("/{cr_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    result = await db.execute(
        select(Comment)
        .where(Comment.entity_type == EntityType.change_request, Comment.entity_id == cr_id)
        .order_by(Comment.created_at.asc())
    )
    return result.scalars().all()


@router.post("/{cr_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    body: CommentCreate,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    result = await db.execute(
        select(ChangeRequest).where(ChangeRequest.id == cr_id, ChangeRequest.project_id == project_id)
    )
    cr = result.scalar_one_or_none()
    if cr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")

    comment = Comment(
        entity_type=EntityType.change_request,
        entity_id=cr_id,
        author_id=member.user_id,
        body=body.body,
    )
    db.add(comment)
    await db.flush()

    if cr.author_id != member.user_id:
        await create_notification(
            db, cr.author_id, tenant_id, "comment.added",
            "change_request", cr.id, f"New comment on CR: {cr.title}",
        )
    await db.refresh(comment)
    return comment
