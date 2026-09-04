import math
import re
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.middleware.auth import require_role
from app.models.audit_log_entry import AuditLogEntry
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.models.tenant_member import MemberRole
from app.schemas.users import UserBrief


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID | None = None
    user: UserBrief | None = None
    event_type: str
    action: str = ""  # mirrors event_type; set explicitly after model_validate
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    entity_label: str | None = None
    summary: str | None = None
    details: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    pages: int


router = APIRouter(prefix="/tenants/{tenant_id}/audit-log", tags=["audit_log"])


@router.get("", response_model=AuditLogListResponse)
async def list_audit_log(
    tenant_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: str | None = Query(None, description="Case-insensitive substring match on event type"),
    event_type: str | None = Query(None, description="Exact match on event type (legacy)"),
    entity_type: str | None = Query(None),
    user_id: uuid.UUID | None = Query(None),
    from_dt: datetime | None = Query(None, alias="from"),
    to_dt: datetime | None = Query(None, alias="to"),
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin)),
):
    query: dict = {"tenantId": tenant_id}
    if action is not None:
        query["eventType"] = {"$regex": re.escape(action), "$options": "i"}
    elif event_type is not None:
        query["eventType"] = event_type
    if entity_type is not None:
        query["entityType"] = entity_type
    if user_id is not None:
        query["userId"] = user_id
    if from_dt is not None or to_dt is not None:
        range_query: dict = {}
        if from_dt is not None:
            range_query["$gte"] = from_dt
        if to_dt is not None:
            range_query["$lte"] = to_dt
        query["createdAt"] = range_query

    total = await AuditLogEntry.find(query).count()
    skip = (page - 1) * page_size
    items = (
        await AuditLogEntry.find(query)
        .sort([("createdAt", -1)])
        .skip(skip)
        .limit(page_size)
        .to_list()
    )

    # Batch-resolve users for the current page (single query, avoids N+1)
    user_ids = {i.user_id for i in items if i.user_id is not None}
    users_by_id: dict[uuid.UUID, User] = {}
    if user_ids:
        users = await User.find({"_id": {"$in": list(user_ids)}}).to_list()
        users_by_id = {u.id: u for u in users}

    item_responses = []
    for i in items:
        u = users_by_id.get(i.user_id) if i.user_id is not None else None
        resp = AuditLogResponse.model_validate(i)
        resp.action = i.event_type
        resp.user = (
            UserBrief(id=u.id, display_name=u.display_name, email=u.email)
            if u is not None
            else None
        )
        item_responses.append(resp)

    return AuditLogListResponse(
        items=item_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )
