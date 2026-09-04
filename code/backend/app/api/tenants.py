import uuid
from typing import Any

from fastapi import APIRouter, Depends, status

from app.dependencies import get_tenant_service
from app.middleware.auth import get_current_tenant_member, get_current_user, require_role
from app.models.tenant_member import MemberRole, TenantMember
from app.models.user import User
from app.schemas.tenants import (
    InvitationCreate,
    InvitationListResponse,
    InvitationResponse,
    MemberResponse,
    TenantCreate,
    TenantResponse,
    TenantUpdate,
)
from app.services.tenants import TenantService

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    body: TenantCreate,
    current_user: User = Depends(get_current_user),
    svc: TenantService = Depends(get_tenant_service),
) -> TenantResponse:
    return TenantResponse.model_validate(await svc.create_tenant(body, current_user.id))


@router.get("", response_model=list[TenantResponse])
async def list_tenants(
    current_user: User = Depends(get_current_user),
    svc: TenantService = Depends(get_tenant_service),
) -> list[TenantResponse]:
    tenants = await svc.list_tenants_for_user(current_user.id)
    return [TenantResponse.model_validate(t) for t in tenants]


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: TenantService = Depends(get_tenant_service),
) -> TenantResponse:
    return TenantResponse.model_validate(await svc.get_tenant_or_404(tenant_id))


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: uuid.UUID,
    body: TenantUpdate,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin)),
    svc: TenantService = Depends(get_tenant_service),
) -> TenantResponse:
    return TenantResponse.model_validate(await svc.update_tenant(tenant_id, body, member.user_id))


@router.get("/{tenant_id}/members", response_model=list[MemberResponse])
async def list_members(
    tenant_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: TenantService = Depends(get_tenant_service),
) -> list[MemberResponse]:
    rows = await svc.list_members(tenant_id)
    return [
        MemberResponse(
            id=m.id,
            user_id=m.user_id,
            email=u.email,
            display_name=u.display_name,
            role=m.role,
            joined_at=m.joined_at,
        )
        for m, u in rows
    ]


@router.post(
    "/{tenant_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_member(
    tenant_id: uuid.UUID,
    body: InvitationCreate,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin)),
    svc: TenantService = Depends(get_tenant_service),
) -> InvitationResponse:
    return InvitationResponse.model_validate(
        await svc.invite_member(tenant_id, body, member.user_id)
    )


@router.get("/{tenant_id}/invitations", response_model=list[InvitationListResponse])
async def list_invitations(
    tenant_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: TenantService = Depends(get_tenant_service),
) -> list[InvitationListResponse]:
    entries = await svc.list_invitations(tenant_id)
    return [
        InvitationListResponse(
            id=entry["invitation"].id,
            tenant_id=entry["invitation"].tenant_id,
            email=entry["invitation"].email,
            role=entry["invitation"].role,
            expires_at=entry["invitation"].expires_at,
            accepted_at=entry["invitation"].accepted_at,
            created_at=entry["invitation"].created_at,
            status=entry["status"],
        )
        for entry in entries
    ]


@router.delete("/{tenant_id}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_invitation(
    tenant_id: uuid.UUID,
    invitation_id: uuid.UUID,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin)),
    svc: TenantService = Depends(get_tenant_service),
) -> None:
    await svc.cancel_invitation(tenant_id, invitation_id, member.user_id)


@router.get("/invitations/{token}/verify")
async def verify_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    svc: TenantService = Depends(get_tenant_service),
) -> dict[str, Any]:
    return await svc.verify_invitation(token, current_user.email)


@router.post("/invitations/{token}/accept", response_model=MemberResponse)
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    svc: TenantService = Depends(get_tenant_service),
) -> MemberResponse:
    member = await svc.accept_invitation(token, current_user)
    return MemberResponse(
        id=member.id,
        user_id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        role=member.role,
        joined_at=member.joined_at,
    )


@router.delete("/{tenant_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin)),
    svc: TenantService = Depends(get_tenant_service),
) -> None:
    await svc.remove_member(tenant_id, user_id, member.user_id)
