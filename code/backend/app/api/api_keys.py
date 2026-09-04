import uuid

from fastapi import APIRouter, Depends, status

from app.dependencies import get_api_key_service
from app.middleware.auth import get_current_tenant_member, require_role
from app.models.tenant_member import MemberRole, TenantMember
from app.schemas.api_keys import ApiKeyCreate, ApiKeyCreatedResponse, ApiKeyResponse
from app.services.api_keys import ApiKeyService

router = APIRouter(
    prefix="/tenants/{tenant_id}/projects/{project_id}/api-keys",
    tags=["api_keys"],
)


@router.post("", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: ApiKeyCreate,
    member: TenantMember = Depends(
        require_role(MemberRole.owner, MemberRole.admin, MemberRole.member)
    ),
    svc: ApiKeyService = Depends(get_api_key_service),
) -> ApiKeyCreatedResponse:
    return await svc.create_api_key(tenant_id, project_id, body, member.user_id)


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: ApiKeyService = Depends(get_api_key_service),
) -> list[ApiKeyResponse]:
    return await svc.list_api_keys(tenant_id, project_id)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    key_id: uuid.UUID,
    member: TenantMember = Depends(
        require_role(MemberRole.owner, MemberRole.admin, MemberRole.member)
    ),
    svc: ApiKeyService = Depends(get_api_key_service),
) -> None:
    await svc.revoke_api_key(tenant_id, project_id, key_id, member.user_id)
