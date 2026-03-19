import math
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_tenant_member
from app.models.bug import Bug, BugStatus
from app.models.comment import Comment, EntityType
from app.models.project import Project
from app.models.tenant_member import TenantMember
from app.schemas.bugs import BugCreate, BugListResponse, BugResponse, BugTransition, BugUpdate
from app.schemas.comments import CommentCreate, CommentResponse
from app.services.audit import log_event
from app.services.notifications import create_notification

router = APIRouter(
    prefix="/tenants/{tenant_id}/projects/{project_id}/bugs",
    tags=["bugs"],
)


async def _get_project(db: AsyncSession, tenant_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.tenant_id == tenant_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("", response_model=BugResponse, status_code=status.HTTP_201_CREATED)
async def create_bug(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: BugCreate,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    bug = Bug(
        project_id=project_id,
        title=body.title,
        body=body.body,
        severity=body.severity,
        author_id=member.user_id,
        assignee_id=body.assignee_id,
    )
    db.add(bug)
    await db.flush()

    await log_event(db, tenant_id, member.user_id, "bug.created", "bug", bug.id)

    if body.assignee_id and body.assignee_id != member.user_id:
        await create_notification(
            db, body.assignee_id, tenant_id, "bug.assigned",
            "bug", bug.id, f"You were assigned to bug: {bug.title}",
        )
    await db.refresh(bug)
    return bug


@router.get("", response_model=BugListResponse)
async def list_bugs(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: BugStatus | None = Query(None, alias="status"),
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    query = select(Bug).where(Bug.project_id == project_id)
    count_query = select(func.count()).select_from(Bug).where(Bug.project_id == project_id)

    if status_filter is not None:
        query = query.where(Bug.status == status_filter)
        count_query = count_query.where(Bug.status == status_filter)
    else:
        query = query.where(Bug.status != BugStatus.deleted)
        count_query = count_query.where(Bug.status != BugStatus.deleted)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Bug.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return BugListResponse(
        items=[BugResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/{bug_id}", response_model=BugResponse)
async def get_bug(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    result = await db.execute(
        select(Bug).where(Bug.id == bug_id, Bug.project_id == project_id)
    )
    bug = result.scalar_one_or_none()
    if bug is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")
    return bug


@router.patch("/{bug_id}", response_model=BugResponse)
async def update_bug(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    body: BugUpdate,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    result = await db.execute(
        select(Bug).where(Bug.id == bug_id, Bug.project_id == project_id)
    )
    bug = result.scalar_one_or_none()
    if bug is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    if body.title is not None:
        bug.title = body.title
    if body.body is not None:
        bug.body = body.body
    if body.severity is not None:
        bug.severity = body.severity
    if body.assignee_id is not None:
        bug.assignee_id = body.assignee_id
    await db.flush()

    await log_event(db, tenant_id, member.user_id, "bug.updated", "bug", bug.id)
    await db.refresh(bug)
    return bug


@router.post("/{bug_id}/transition", response_model=BugResponse)
async def transition_bug(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    body: BugTransition,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    result = await db.execute(
        select(Bug).where(Bug.id == bug_id, Bug.project_id == project_id)
    )
    bug = result.scalar_one_or_none()
    if bug is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    bug.status = body.status
    if body.status in (BugStatus.closed, BugStatus.resolved, BugStatus.wont_fix):
        bug.closed_at = datetime.now(timezone.utc)
    await db.flush()

    await log_event(
        db, tenant_id, member.user_id, "bug.transitioned", "bug", bug.id,
        details={"new_status": body.status.value},
    )

    if bug.author_id != member.user_id:
        await create_notification(
            db, bug.author_id, tenant_id, "bug.transitioned",
            "bug", bug.id, f"Bug '{bug.title}' moved to {body.status.value}",
        )
    await db.refresh(bug)
    return bug


@router.get("/{bug_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    result = await db.execute(
        select(Comment)
        .where(Comment.entity_type == EntityType.bug, Comment.entity_id == bug_id)
        .order_by(Comment.created_at.asc())
    )
    return result.scalars().all()


@router.post("/{bug_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    body: CommentCreate,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    result = await db.execute(
        select(Bug).where(Bug.id == bug_id, Bug.project_id == project_id)
    )
    bug = result.scalar_one_or_none()
    if bug is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    comment = Comment(
        entity_type=EntityType.bug,
        entity_id=bug_id,
        author_id=member.user_id,
        body=body.body,
    )
    db.add(comment)
    await db.flush()

    if bug.author_id != member.user_id:
        await create_notification(
            db, bug.author_id, tenant_id, "comment.added",
            "bug", bug.id, f"New comment on bug: {bug.title}",
        )
    await db.refresh(comment)
    return comment
