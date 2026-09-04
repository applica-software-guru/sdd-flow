import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.dependencies import get_audit_service
from app.middleware.auth import require_role
from app.models.tenant_member import MemberRole, TenantMember
from app.schemas.users import UserBrief
from app.services.audit import AuditService


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
    details: dict[str, Any] | None = None
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
    svc: AuditService = Depends(get_audit_service),
) -> AuditLogListResponse:
    pairs, total, pages = await svc.query_audit_log(
        tenant_id,
        page=page,
        page_size=page_size,
        action=action,
        event_type=event_type,
        entity_type=entity_type,
        user_id=user_id,
        from_dt=from_dt,
        to_dt=to_dt,
    )

    item_responses: list[AuditLogResponse] = []
    for i, u in pairs:
        resp = AuditLogResponse.model_validate(i)
        resp.action = i.event_type
        resp.user = u
        item_responses.append(resp)

    return AuditLogListResponse(
        items=item_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
