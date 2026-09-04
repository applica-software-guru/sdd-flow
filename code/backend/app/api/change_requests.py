import math
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.middleware.auth import get_current_tenant_member
from app.models.change_request import CRStatus, ChangeRequest
from app.models.comment import Comment, EntityType
from app.models.tenant_member import TenantMember
from app.repositories import (
    AssignmentRepository,
    ChangeRequestRepository,
    CommentRepository,
    ProjectRepository,
)
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
from app.services.assignment import apply_assignment, record_initial_assignment
from app.services.audit import log_event
from app.services.notifications import create_notification
from app.services.slug import assign_number_and_slug, slugify
from app.services.users import ensure_tenant_member, resolve_user_briefs

router = APIRouter(
    prefix="/tenants/{tenant_id}/projects/{project_id}/change-requests",
    tags=["change_requests"],
)


async def _get_project(tenant_id: uuid.UUID, project_id: uuid.UUID):
    project_repo = ProjectRepository()
    project = await project_repo.find_by_id(project_id)
    if project is None or project.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def _attach_users(responses: list[CRResponse], entities: list[ChangeRequest]) -> list[CRResponse]:
    """Attach resolved author/assignee UserBrief objects (batch, no N+1)."""
    user_ids: set[uuid.UUID] = set()
    for e in entities:
        user_ids.add(e.author_id)
        if e.assignee_id is not None:
            user_ids.add(e.assignee_id)
    users = await resolve_user_briefs(user_ids)
    for resp, e in zip(responses, entities):
        resp.author = users.get(e.author_id)
        resp.assignee = users.get(e.assignee_id) if e.assignee_id is not None else None
    return responses


@router.post("", response_model=CRResponse, status_code=status.HTTP_201_CREATED)
async def create_cr(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: CRCreate,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    if body.assignee_id is not None:
        await ensure_tenant_member(tenant_id, body.assignee_id)
    cr_repo = ChangeRequestRepository()
    cr = ChangeRequest(
        project_id=project_id,
        number=0,
        slug="",
        title=body.title,
        body=body.body,
        author_id=member.user_id,
        assignee_id=body.assignee_id,
        target_files=body.target_files or [],
    )
    await assign_number_and_slug(cr, project_id, body.title, explicit_slug=body.slug, repo=cr_repo)

    await log_event(
        tenant_id, member.user_id, "cr.created", "change_request", cr.id,
        entity_label=cr.title, summary="created",
    )
    await record_initial_assignment(tenant_id, member.user_id, cr, "change_request")

    if body.assignee_id and body.assignee_id != member.user_id:
        await create_notification(
            body.assignee_id, tenant_id, "cr.assigned",
            "change_request", cr.id, f"You were assigned to CR: {cr.title}",
        )
    return cr


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
):
    await _get_project(tenant_id, project_id)

    if status_filter is None:
        query: dict = {"projectId": project_id, "status": {"$ne": CRStatus.deleted.value}}
    else:
        query = {"projectId": project_id, "status": status_filter.value}
    if author_id is not None:
        query["authorId"] = author_id
    if assignee_id is not None:
        query["assigneeId"] = assignee_id

    total = await ChangeRequest.find(query).count()
    skip = (page - 1) * page_size
    items = await ChangeRequest.find(query).sort([("number", -1)]).skip(skip).limit(page_size).to_list()

    responses = await _attach_users([CRResponse.model_validate(i) for i in items], items)
    return CRListResponse(
        items=responses,
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
):
    await _get_project(tenant_id, project_id)
    cr_repo = ChangeRequestRepository()
    cr = await cr_repo.find_by_id(cr_id)
    if cr is None or cr.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")
    resp = CRResponse.model_validate(cr)
    return (await _attach_users([resp], [cr]))[0]


@router.patch("/{cr_id}", response_model=CRResponse)
async def update_cr(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    body: CRUpdate,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    cr_repo = ChangeRequestRepository()
    cr = await cr_repo.find_by_id(cr_id)
    if cr is None or cr.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")

    updates = {}
    if body.title is not None:
        updates[ChangeRequest.title] = body.title
    if body.body is not None:
        updates[ChangeRequest.body] = body.body
    if body.target_files is not None:
        updates[ChangeRequest.target_files] = body.target_files
    if body.slug is not None:
        new_slug = slugify(body.slug)
        existing = await cr_repo.find_by_slug(project_id, new_slug)
        if existing is not None and existing.id != cr_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already in use")
        updates[ChangeRequest.slug] = new_slug

    if updates:
        await cr.set(updates)

    # Assignment changes are routed through the shared assignment flow
    # (validation, audit cr.assigned, notification, history) — PATCH keeps
    # supporting assignee_id for backwards compatibility; None means "not
    # provided" (use POST /assign to unassign).
    if body.assignee_id is not None:
        await apply_assignment(tenant_id, member.user_id, cr, "change_request", body.assignee_id)

    await log_event(
        tenant_id, member.user_id, "cr.updated", "change_request", cr.id,
        entity_label=cr.title, summary="updated",
    )
    cr = await cr_repo.find_by_id(cr_id)
    resp = CRResponse.model_validate(cr)
    return (await _attach_users([resp], [cr]))[0]


@router.post("/{cr_id}/assign", response_model=CRResponse)
async def assign_cr(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    body: AssignCR,
    member: TenantMember = Depends(get_current_tenant_member),
):
    """Assign the CR to a tenant member (or unassign with assignee_id=null)."""
    await _get_project(tenant_id, project_id)
    cr_repo = ChangeRequestRepository()
    cr = await cr_repo.find_by_id(cr_id)
    if cr is None or cr.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")

    await apply_assignment(tenant_id, member.user_id, cr, "change_request", body.assignee_id)

    cr = await cr_repo.find_by_id(cr_id)
    resp = CRResponse.model_validate(cr)
    return (await _attach_users([resp], [cr]))[0]


@router.get("/{cr_id}/assignments", response_model=list[AssignmentEntryResponse])
async def list_cr_assignments(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
):
    """Append-only assignment history for the CR (newest first)."""
    await _get_project(tenant_id, project_id)
    cr_repo = ChangeRequestRepository()
    cr = await cr_repo.find_by_id(cr_id)
    if cr is None or cr.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")

    entries = await AssignmentRepository().find_by_entity("change_request", cr_id)
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


@router.post("/{cr_id}/transition", response_model=CRResponse)
async def transition_cr(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    body: CRTransition,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    cr_repo = ChangeRequestRepository()
    cr = await cr_repo.find_by_id(cr_id)
    if cr is None or cr.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")

    if cr.status in (CRStatus.deleted, CRStatus.closed):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot transition a {cr.status.value} item")

    old_status = cr.status
    updates: dict = {ChangeRequest.status: body.status}
    if body.status in (CRStatus.closed, CRStatus.applied, CRStatus.rejected):
        updates[ChangeRequest.closed_at] = datetime.now(timezone.utc)
    await cr.set(updates)

    await log_event(
        tenant_id, member.user_id, "cr.transitioned", "change_request", cr.id,
        entity_label=cr.title,
        summary=f"status: {old_status.value} → {body.status.value}",
        details={"old_status": old_status.value, "new_status": body.status.value},
    )

    if cr.author_id != member.user_id:
        await create_notification(
            cr.author_id, tenant_id, "cr.transitioned",
            "change_request", cr.id, f"CR '{cr.title}' moved to {body.status.value}",
        )
    cr = await cr_repo.find_by_id(cr_id)
    return cr


@router.get("/{cr_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    comment_repo = CommentRepository()
    return await comment_repo.find_by_entity(EntityType.change_request.value, cr_id)


@router.post("/{cr_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    cr_id: uuid.UUID,
    body: CommentCreate,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    cr_repo = ChangeRequestRepository()
    cr = await cr_repo.find_by_id(cr_id)
    if cr is None or cr.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")

    comment = Comment(
        entity_type=EntityType.change_request,
        entity_id=cr_id,
        author_id=member.user_id,
        body=body.body,
    )
    await comment.insert()

    if cr.author_id != member.user_id:
        await create_notification(
            cr.author_id, tenant_id, "comment.added",
            "change_request", cr.id, f"New comment on CR: {cr.title}",
        )
    return comment
