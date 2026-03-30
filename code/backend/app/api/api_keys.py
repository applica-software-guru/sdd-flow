import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth import get_current_tenant_member, require_role
from app.models.api_key import ApiKey
from app.models.tenant_member import MemberRole, TenantMember
from app.repositories import ProjectRepository
from app.schemas.api_keys import ApiKeyCreate, ApiKeyCreatedResponse, ApiKeyResponse
from app.services.audit import log_event

router = APIRouter(
    prefix="/tenants/{tenant_id}/projects/{project_id}/api-keys",
    tags=["api_keys"],
)


async def _get_project(tenant_id: uuid.UUID, project_id: uuid.UUID):
    project_repo = ProjectRepository()
    project = await project_repo.find_by_id(project_id)
    if project is None or project.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: ApiKeyCreate,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin, MemberRole.member)),
):
    await _get_project(tenant_id, project_id)

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
    await api_key.insert()

    await log_event(tenant_id, member.user_id, "api_key.created", "api_key", api_key.id)

    base = ApiKeyResponse.model_validate(api_key, from_attributes=True)
    return ApiKeyCreatedResponse(**base.model_dump(), full_key=raw_key)


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
):
    await _get_project(tenant_id, project_id)
    api_keys = await ApiKey.find(
        {"projectId": project_id}
    ).sort([("createdAt", -1)]).to_list()
    return api_keys


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    key_id: uuid.UUID,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin, MemberRole.member)),
):
    await _get_project(tenant_id, project_id)
    api_key = await ApiKey.get(key_id)
    if api_key is None or api_key.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    await api_key.set({ApiKey.revoked_at: datetime.now(timezone.utc)})

    await log_event(tenant_id, member.user_id, "api_key.revoked", "api_key", api_key.id)
