import math
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.middleware.auth import get_current_tenant_member
from app.models.bug import Bug, BugStatus
from app.models.comment import Comment, EntityType
from app.models.tenant_member import TenantMember
from app.repositories import BugRepository, CommentRepository, ProjectRepository
from app.schemas.bugs import BugCreate, BugListResponse, BugResponse, BugTransition, BugUpdate
from app.schemas.comments import CommentCreate, CommentResponse
from app.services.audit import log_event
from app.services.notifications import create_notification
from app.services.slug import assign_number_and_slug

router = APIRouter(
    prefix="/tenants/{tenant_id}/projects/{project_id}/bugs",
    tags=["bugs"],
)


async def _get_project(tenant_id: uuid.UUID, project_id: uuid.UUID):
    project_repo = ProjectRepository()
    project = await project_repo.find_by_id(project_id)
    if project is None or project.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("", response_model=BugResponse, status_code=status.HTTP_201_CREATED)
async def create_bug(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: BugCreate,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    bug_repo = BugRepository()
    bug = Bug(
        project_id=project_id,
        number=0,
        slug="",
        title=body.title,
        body=body.body,
        severity=body.severity,
        author_id=member.user_id,
        assignee_id=body.assignee_id,
    )
    await assign_number_and_slug(bug, project_id, body.title, repo=bug_repo)

    await log_event(tenant_id, member.user_id, "bug.created", "bug", bug.id)

    if body.assignee_id and body.assignee_id != member.user_id:
        await create_notification(
            body.assignee_id, tenant_id, "bug.assigned",
            "bug", bug.id, f"You were assigned to bug: {bug.title}",
        )
    return bug


@router.get("", response_model=BugListResponse)
async def list_bugs(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: BugStatus | None = Query(None, alias="status"),
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)

    if status_filter is None:
        query: dict = {"projectId": project_id, "status": {"$ne": BugStatus.deleted.value}}
    else:
        query = {"projectId": project_id, "status": status_filter.value}

    total = await Bug.find(query).count()
    skip = (page - 1) * page_size
    items = await Bug.find(query).sort([("createdAt", -1)]).skip(skip).limit(page_size).to_list()

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
):
    await _get_project(tenant_id, project_id)
    bug_repo = BugRepository()
    bug = await bug_repo.find_by_id(bug_id)
    if bug is None or bug.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")
    return bug


@router.patch("/{bug_id}", response_model=BugResponse)
async def update_bug(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    body: BugUpdate,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    bug_repo = BugRepository()
    bug = await bug_repo.find_by_id(bug_id)
    if bug is None or bug.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    updates = {}
    if body.title is not None:
        updates[Bug.title] = body.title
    if body.body is not None:
        updates[Bug.body] = body.body
    if body.severity is not None:
        updates[Bug.severity] = body.severity
    if body.assignee_id is not None:
        updates[Bug.assignee_id] = body.assignee_id

    if updates:
        await bug.set(updates)

    await log_event(tenant_id, member.user_id, "bug.updated", "bug", bug.id)
    bug = await bug_repo.find_by_id(bug_id)
    return bug


@router.post("/{bug_id}/transition", response_model=BugResponse)
async def transition_bug(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    body: BugTransition,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    bug_repo = BugRepository()
    bug = await bug_repo.find_by_id(bug_id)
    if bug is None or bug.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    if bug.status in (BugStatus.deleted, BugStatus.closed):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot transition a {bug.status.value} item")

    updates: dict = {Bug.status: body.status}
    if body.status in (BugStatus.closed, BugStatus.resolved, BugStatus.wont_fix):
        updates[Bug.closed_at] = datetime.now(timezone.utc)
    await bug.set(updates)

    await log_event(
        tenant_id, member.user_id, "bug.transitioned", "bug", bug.id,
        details={"new_status": body.status.value},
    )

    if bug.author_id != member.user_id:
        await create_notification(
            bug.author_id, tenant_id, "bug.transitioned",
            "bug", bug.id, f"Bug '{bug.title}' moved to {body.status.value}",
        )
    bug = await bug_repo.find_by_id(bug_id)
    return bug


@router.get("/{bug_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    comment_repo = CommentRepository()
    return await comment_repo.find_by_entity(EntityType.bug.value, bug_id)


@router.post("/{bug_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    body: CommentCreate,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    bug_repo = BugRepository()
    bug = await bug_repo.find_by_id(bug_id)
    if bug is None or bug.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    comment = Comment(
        entity_type=EntityType.bug,
        entity_id=bug_id,
        author_id=member.user_id,
        body=body.body,
    )
    await comment.insert()

    if bug.author_id != member.user_id:
        await create_notification(
            bug.author_id, tenant_id, "comment.added",
            "bug", bug.id, f"New comment on bug: {bug.title}",
        )
    return comment
