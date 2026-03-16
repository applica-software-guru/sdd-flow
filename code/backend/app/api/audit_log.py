import math
import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_tenant_member
from app.models.audit_log_entry import AuditLogEntry
from app.models.tenant_member import TenantMember
from datetime import datetime


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
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLogEntry).where(AuditLogEntry.tenant_id == tenant_id)
    count_query = select(func.count()).select_from(AuditLogEntry).where(AuditLogEntry.tenant_id == tenant_id)

    if event_type is not None:
        query = query.where(AuditLogEntry.event_type == event_type)
        count_query = count_query.where(AuditLogEntry.event_type == event_type)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(AuditLogEntry.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )
