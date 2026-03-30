import math
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.middleware.auth import get_current_tenant_member
from app.models.audit_log_entry import AuditLogEntry
from app.models.tenant_member import TenantMember
from app.repositories import AuditRepository


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID | None = None
    event_type: str
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
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
    event_type: str | None = Query(None),
    member: TenantMember = Depends(get_current_tenant_member),
):
    if event_type is not None:
        # Filter by exact event_type
        query: dict = {"tenantId": tenant_id, "eventType": event_type}
    else:
        query = {"tenantId": tenant_id}

    total = await AuditLogEntry.find(query).count()
    skip = (page - 1) * page_size
    items = (
        await AuditLogEntry.find(query)
        .sort([("createdAt", -1)])
        .skip(skip)
        .limit(page_size)
        .to_list()
    )

    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )
