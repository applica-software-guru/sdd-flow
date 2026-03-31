import math
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.middleware.auth import get_current_tenant_member
from app.models.change_request import CRStatus, ChangeRequest
from app.models.comment import Comment, EntityType
from app.models.tenant_member import TenantMember
from app.repositories import ChangeRequestRepository, CommentRepository, ProjectRepository
from app.schemas.change_requests import CRCreate, CRListResponse, CRResponse, CRTransition, CRUpdate
from app.schemas.comments import CommentCreate, CommentResponse
from app.services.audit import log_event
from app.services.notifications import create_notification
from app.services.slug import assign_number_and_slug

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


@router.post("", response_model=CRResponse, status_code=status.HTTP_201_CREATED)
async def create_cr(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: CRCreate,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
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
    await assign_number_and_slug(cr, project_id, body.title, repo=cr_repo)

    await log_event(tenant_id, member.user_id, "cr.created", "change_request", cr.id)

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
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)

    if status_filter is None:
        query: dict = {"projectId": project_id, "status": {"$ne": CRStatus.deleted.value}}
    else:
        query = {"projectId": project_id, "status": status_filter.value}

    total = await ChangeRequest.find(query).count()
    skip = (page - 1) * page_size
    items = await ChangeRequest.find(query).sort([("number", -1)]).skip(skip).limit(page_size).to_list()

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
):
    await _get_project(tenant_id, project_id)
    cr_repo = ChangeRequestRepository()
    cr = await cr_repo.find_by_id(cr_id)
    if cr is None or cr.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")
    return cr


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
    if body.assignee_id is not None:
        updates[ChangeRequest.assignee_id] = body.assignee_id
    if body.target_files is not None:
        updates[ChangeRequest.target_files] = body.target_files

    if updates:
        await cr.set(updates)

    await log_event(tenant_id, member.user_id, "cr.updated", "change_request", cr.id)
    cr = await cr_repo.find_by_id(cr_id)
    return cr


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

    updates: dict = {ChangeRequest.status: body.status}
    if body.status in (CRStatus.closed, CRStatus.applied, CRStatus.rejected):
        updates[ChangeRequest.closed_at] = datetime.now(timezone.utc)
    await cr.set(updates)

    await log_event(
        tenant_id, member.user_id, "cr.transitioned", "change_request", cr.id,
        details={"new_status": body.status.value},
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
