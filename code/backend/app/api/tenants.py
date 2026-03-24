import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_tenant_member, get_current_user, require_role
from app.models.tenant import Tenant
from app.models.tenant_invitation import TenantInvitation
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
from app.services.audit import log_event
from app.services.invitations import send_tenant_invitation_email

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _compute_invitation_status(invitation: TenantInvitation) -> str:
    if invitation.accepted_at is not None:
        return "accepted"

    now = datetime.now(timezone.utc)
    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < now:
        return "expired"

    return "pending"


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    body: TenantCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.slug == body.slug))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already taken")

    tenant = Tenant(name=body.name, slug=body.slug, default_role=body.default_role)
    db.add(tenant)
    await db.flush()

    member = TenantMember(
        tenant_id=tenant.id,
        user_id=current_user.id,
        role=MemberRole.owner,
    )
    db.add(member)
    await db.flush()

    await log_event(db, tenant.id, current_user.id, "tenant.created", "tenant", tenant.id)
    await db.refresh(tenant)
    return tenant


@router.get("", response_model=list[TenantResponse])
async def list_tenants(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Tenant)
        .join(TenantMember, TenantMember.tenant_id == Tenant.id)
        .where(TenantMember.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return tenant


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: uuid.UUID,
    body: TenantUpdate,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    if body.name is not None:
        tenant.name = body.name
    if body.default_role is not None:
        tenant.default_role = body.default_role
    await db.flush()

    await log_event(db, tenant.id, member.user_id, "tenant.updated", "tenant", tenant.id)
    await db.refresh(tenant)
    return tenant


@router.get("/{tenant_id}/members", response_model=list[MemberResponse])
async def list_members(
    tenant_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TenantMember, User)
        .join(User, TenantMember.user_id == User.id)
        .where(TenantMember.tenant_id == tenant_id)
    )
    rows = result.all()
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


@router.post("/{tenant_id}/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    tenant_id: uuid.UUID,
    body: InvitationCreate,
    member: TenantMember = Depends(require_role(MemberRole.owner, MemberRole.admin)),
    db: AsyncSession = Depends(get_db),
):
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    # Check if already a member
    result = await db.execute(
        select(TenantMember)
        .join(User, TenantMember.user_id == User.id)
        .where(TenantMember.tenant_id == tenant_id, User.email == body.email)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member")

    invitation = TenantInvitation(
        tenant_id=tenant_id,
        email=body.email,
        role=body.role,
        invited_by=member.user_id,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(invitation)
    await db.flush()

    await log_event(
        db, tenant_id, member.user_id, "invitation.created", "invitation", invitation.id,
        details={"email": body.email, "role": body.role.value},
    )

    inviter_result = await db.execute(select(User).where(User.id == member.user_id))
    inviter = inviter_result.scalar_one_or_none()
    inviter_name = inviter.display_name if inviter is not None else "A team member"

    await send_tenant_invitation_email(
        recipient_email=body.email,
        tenant_name=tenant.name,
        inviter_name=inviter_name,
        role=body.role.value,
        token=invitation.token,
    )

    await db.refresh(invitation)
    return invitation


@router.get("/{tenant_id}/invitations", response_model=list[InvitationListResponse])
async def list_invitations(
    tenant_id: uuid.UUID,
    member: TenantMember = Depends(get_current_tenant_member),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TenantInvitation)
        .where(TenantInvitation.tenant_id == tenant_id)
        .order_by(TenantInvitation.created_at.desc())
    )
    invitations = result.scalars().all()

    return [
        InvitationListResponse(
            id=invitation.id,
            tenant_id=invitation.tenant_id,
            email=invitation.email,
            role=invitation.role,
            expires_at=invitation.expires_at,
            accepted_at=invitation.accepted_at,
            created_at=invitation.created_at,
            status=_compute_invitation_status(invitation),
        )
        for invitation in invitations
    ]


@router.get("/invitations/{token}/verify")
async def verify_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TenantInvitation).where(TenantInvitation.token == token)
    )
    invitation = result.scalar_one_or_none()
    if invitation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    if invitation.email != current_user.email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invitation is for a different email")

    if invitation.accepted_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation already accepted")

    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation expired")

    tenant_result = await db.execute(select(Tenant).where(Tenant.id == invitation.tenant_id))
    tenant = tenant_result.scalar_one_or_none()

    return {
        "email": invitation.email,
        "role": invitation.role.value,
        "tenant_name": tenant.name if tenant else "Unknown",
        "expires_at": invitation.expires_at.isoformat(),
    }


@router.post("/invitations/{token}/accept", response_model=MemberResponse)
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TenantInvitation).where(TenantInvitation.token == token)
    )
    invitation = result.scalar_one_or_none()
    if invitation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    if invitation.email != current_user.email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invitation is for a different email")

    if invitation.accepted_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation already accepted")

    if invitation.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation expired")

    # Check not already member
    result = await db.execute(
        select(TenantMember).where(
            TenantMember.tenant_id == invitation.tenant_id,
            TenantMember.user_id == current_user.id,
        )
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already a member")

    member = TenantMember(
        tenant_id=invitation.tenant_id,
        user_id=current_user.id,
        role=invitation.role,
        invited_by=invitation.invited_by,
    )
    db.add(member)
    invitation.accepted_at = datetime.now(timezone.utc)
    await db.flush()

    await log_event(
        db, invitation.tenant_id, current_user.id, "member.joined", "tenant_member", member.id,
    )
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
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TenantMember).where(
            TenantMember.tenant_id == tenant_id,
            TenantMember.user_id == user_id,
        )
    )
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if target.role == MemberRole.owner and member.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot remove owner")

    await db.delete(target)
    await db.flush()

    await log_event(
        db, tenant_id, member.user_id, "member.removed", "tenant_member", target.id,
        details={"removed_user_id": str(user_id)},
    )
