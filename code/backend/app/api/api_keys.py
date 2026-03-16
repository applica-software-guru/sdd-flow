import hashlib
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_tenant_member, require_role
from app.models.api_key import ApiKey
from app.models.project import Project
from app.models.tenant_member import MemberRole, TenantMember
from app.schemas.api_keys import ApiKeyCreate, ApiKeyCreatedResponse, ApiKeyResponse
from app.services.audit import log_event

router = APIRouter(
    prefix="/tenants/{tenant_id}/projects/{project_id}/api-keys",
    tags=["api_keys"],
)


async def _get_project(db: AsyncSession, tenant_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.tenant_id == tenant_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: ApiKeyCreate,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin, MemberRole.member)),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)

    raw_key = f"sdd_{secrets.token_urlsafe(32)}"
    key_prefix = raw_key[:12]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    api_key = ApiKey(
        project_id=project_id,
        name=body.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        created_by=member.user_id,
    )
    db.add(api_key)
    await db.flush()

    await log_event(db, tenant_id, member.user_id, "api_key.created", "api_key", api_key.id)
    await db.refresh(api_key)

    base = ApiKeyResponse.model_validate(api_key, from_attributes=True)
    return ApiKeyCreatedResponse(**base.model_dump(), full_key=raw_key)


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.project_id == project_id)
        .order_by(ApiKey.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    key_id: uuid.UUID,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin, MemberRole.member)),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(db, tenant_id, project_id)
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.project_id == project_id)
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    from datetime import datetime, timezone
    api_key.revoked_at = datetime.now(timezone.utc)
    await db.flush()

    await log_event(db, tenant_id, member.user_id, "api_key.revoked", "api_key", api_key.id)
