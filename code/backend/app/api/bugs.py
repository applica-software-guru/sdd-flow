import math
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.middleware.auth import get_current_tenant_member
from app.models.bug import Bug, BugSeverity, BugStatus
from app.models.comment import Comment, EntityType
from app.models.tenant_member import TenantMember
from app.repositories import (
    AssignmentRepository,
    BugRepository,
    CommentRepository,
    ProjectRepository,
)
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
from app.services.assignment import apply_assignment, record_initial_assignment
from app.services.audit import log_event
from app.services.collab_notifications import notify_comment_added, notify_content_changed
from app.services.notifications import create_notification
from app.services.slug import assign_number_and_slug, slugify
from app.services.users import ensure_tenant_member, resolve_user_briefs

router = APIRouter(
    prefix="/tenants/{tenant_id}/projects/{project_id}/bugs",
    tags=["bugs"],
)


async def _enrich_responses(responses: list[BugResponse], entities: list[Bug]) -> list[BugResponse]:
    """Attach resolved author/assignee UserBrief and batched comments_count (no N+1)."""
    if not responses:
        return responses
    user_ids: set[uuid.UUID] = set()
    for e in entities:
        user_ids.add(e.author_id)
        if e.assignee_id is not None:
            user_ids.add(e.assignee_id)
    users = await resolve_user_briefs(user_ids)

    bug_ids = [e.id for e in entities]
    comment_counts = await CommentRepository().count_by_entities(EntityType.bug.value, bug_ids)

    for resp, e in zip(responses, entities):
        resp.author = users.get(e.author_id)
        resp.assignee = users.get(e.assignee_id) if e.assignee_id is not None else None
        resp.comments_count = comment_counts.get(e.id, 0)
    return responses


async def _attach_comment_authors(comments: list[Comment]) -> list[CommentResponse]:
    """Attach resolved author UserBrief to each comment (batch, no N+1)."""
    author_ids = {c.author_id for c in comments}
    users = await resolve_user_briefs(author_ids)
    responses = [CommentResponse.model_validate(c) for c in comments]
    for resp, c in zip(responses, comments):
        resp.author = users.get(c.author_id)
    return responses


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
    if body.assignee_id is not None:
        await ensure_tenant_member(tenant_id, body.assignee_id)
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
    await assign_number_and_slug(bug, project_id, body.title, explicit_slug=body.slug, repo=bug_repo)

    await log_event(
        tenant_id, member.user_id, "bug.created", "bug", bug.id,
        entity_label=bug.title, summary="created",
    )
    await record_initial_assignment(tenant_id, member.user_id, bug, "bug")

    if body.assignee_id and body.assignee_id != member.user_id:
        await create_notification(
            body.assignee_id, tenant_id, "bug.assigned",
            "bug", bug.id, f"You were assigned to bug: {bug.title}",
        )
    resp = BugResponse.model_validate(bug)
    return (await _enrich_responses([resp], [bug]))[0]


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
):
    await _get_project(tenant_id, project_id)

    if status_filter is None:
        query: dict = {"projectId": project_id, "status": {"$ne": BugStatus.deleted.value}}
    else:
        query = {"projectId": project_id, "status": status_filter.value}

    if severity_filter is not None:
        query["severity"] = severity_filter.value
    if author_id is not None:
        query["authorId"] = author_id
    if assignee_id is not None:
        query["assigneeId"] = assignee_id

    total = await Bug.find(query).count()
    skip = (page - 1) * page_size
    items = await Bug.find(query).sort([("number", -1)]).skip(skip).limit(page_size).to_list()

    responses = await _enrich_responses([BugResponse.model_validate(i) for i in items], items)
    return BugListResponse(
        items=responses,
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
    resp = BugResponse.model_validate(bug)
    return (await _enrich_responses([resp], [bug]))[0]


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
    if body.slug is not None:
        new_slug = slugify(body.slug)
        existing = await bug_repo.find_by_slug(project_id, new_slug)
        if existing is not None and existing.id != bug_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already in use")
        updates[Bug.slug] = new_slug

    project = await _get_project(tenant_id, project_id)

    # Detect real content changes (title/body) before applying updates:
    # no-op saves must not trigger content_changed notifications.
    changed_fields = []
    if body.title is not None and body.title != bug.title:
        changed_fields.append("title")
    if body.body is not None and body.body != bug.body:
        changed_fields.append("body")

    if updates:
        await bug.set(updates)

    if changed_fields:
        await log_event(
            tenant_id, member.user_id, "bug.content_changed", "bug", bug.id,
            entity_label=bug.title,
            summary=f"changed {', '.join(changed_fields)}",
            details={"changed_fields": changed_fields},
        )
        await notify_content_changed(
            tenant_id, member.user_id, EntityType.bug.value,
            bug, changed_fields, project_name=project.name,
        )

    # Assignment changes are routed through the shared assignment flow
    # (validation, audit bug.assigned, notification, history) — PATCH keeps
    # supporting assignee_id for backwards compatibility; None means "not
    # provided" (use POST /assign to unassign).
    if body.assignee_id is not None:
        await apply_assignment(tenant_id, member.user_id, bug, "bug", body.assignee_id)

    await log_event(
        tenant_id, member.user_id, "bug.updated", "bug", bug.id,
        entity_label=bug.title, summary="updated",
    )
    bug = await bug_repo.find_by_id(bug_id)
    resp = BugResponse.model_validate(bug)
    return (await _enrich_responses([resp], [bug]))[0]


@router.post("/{bug_id}/assign", response_model=BugResponse)
async def assign_bug(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    body: AssignBug,
    member: TenantMember = Depends(get_current_tenant_member),
):
    """Assign the bug to a tenant member (or unassign with assignee_id=null)."""
    await _get_project(tenant_id, project_id)
    bug_repo = BugRepository()
    bug = await bug_repo.find_by_id(bug_id)
    if bug is None or bug.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    await apply_assignment(tenant_id, member.user_id, bug, "bug", body.assignee_id)

    bug = await bug_repo.find_by_id(bug_id)
    resp = BugResponse.model_validate(bug)
    return (await _enrich_responses([resp], [bug]))[0]


@router.get("/{bug_id}/assignments", response_model=list[AssignmentEntryResponse])
async def list_bug_assignments(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
):
    """Append-only assignment history for the bug (newest first)."""
    await _get_project(tenant_id, project_id)
    bug_repo = BugRepository()
    bug = await bug_repo.find_by_id(bug_id)
    if bug is None or bug.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    entries = await AssignmentRepository().find_by_entity("bug", bug_id)
    user_ids: set[uuid.UUID] = set()
    for e in entries:
        if e.assignee_id is not None:
            user_ids.add(e.assignee_id)
        if e.assigned_by is not None:
            user_ids.add(e.assigned_by)
    users = await resolve_user_briefs(user_ids)

    return [
        AssignmentEntryResponse(
            id=e.id,
            assignee_id=e.assignee_id,
            assignee=users.get(e.assignee_id) if e.assignee_id is not None else None,
            assigned_by=e.assigned_by,
            assigned_by_name=(users[e.assigned_by].display_name if e.assigned_by in users else None),
            created_at=e.created_at,
        )
        for e in entries
    ]


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

    old_status = bug.status
    updates: dict = {Bug.status: body.status}
    if body.status in (BugStatus.closed, BugStatus.resolved, BugStatus.wont_fix):
        updates[Bug.closed_at] = datetime.now(timezone.utc)
    await bug.set(updates)

    await log_event(
        tenant_id, member.user_id, "bug.transitioned", "bug", bug.id,
        entity_label=bug.title,
        summary=f"status: {old_status.value} → {body.status.value}",
        details={"old_status": old_status.value, "new_status": body.status.value},
    )

    if bug.author_id != member.user_id:
        await create_notification(
            bug.author_id, tenant_id, "bug.transitioned",
            "bug", bug.id, f"Bug '{bug.title}' moved to {body.status.value}",
        )
    bug = await bug_repo.find_by_id(bug_id)
    resp = BugResponse.model_validate(bug)
    return (await _enrich_responses([resp], [bug]))[0]


@router.get("/{bug_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    comment_repo = CommentRepository()
    comments = await comment_repo.find_by_entity(EntityType.bug.value, bug_id)
    return await _attach_comment_authors(comments)


@router.post("/{bug_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    bug_id: uuid.UUID,
    body: CommentCreate,
    member: TenantMember = Depends(get_current_tenant_member),
):
    project = await _get_project(tenant_id, project_id)
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

    await log_event(
        tenant_id, member.user_id, "bug.commented", "bug", bug.id,
        entity_label=bug.title, summary="commented",
    )

    # Notify all actors (author, assignee, previous commenters except the
    # comment author) in-app, plus emails per preference. Best-effort.
    await notify_comment_added(
        tenant_id, member.user_id, EntityType.bug.value,
        bug, comment, project_name=project.name,
    )
    return (await _attach_comment_authors([comment]))[0]
