"""Tenant domain service: tenants, members, invitations."""

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status

from app.models.tenant import Tenant
from app.models.tenant_invitation import TenantInvitation
from app.models.tenant_member import MemberRole, TenantMember
from app.models.user import User
from app.repositories import ProjectRepository, TenantRepository, UserRepository
from app.schemas.tenants import (
    InvitationCreate,
    TenantCreate,
    TenantUpdate,
    WorkspaceNavigationProject,
    WorkspaceNavigationResponse,
    WorkspaceNavigationTenant,
)
from app.services.audit import AuditService
from app.services.invitations import send_tenant_invitation_email


def compute_invitation_status(invitation: TenantInvitation) -> str:
    if invitation.accepted_at is not None:
        return "accepted"

    now = datetime.now(UTC)
    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at < now:
        return "expired"

    return "pending"


class TenantService:
    def __init__(
        self,
        tenant_repo: TenantRepository,
        user_repo: UserRepository,
        audit_service: AuditService,
        project_repo: ProjectRepository,
    ) -> None:
        self._tenant_repo = tenant_repo
        self._user_repo = user_repo
        self._audit_service = audit_service
        self._project_repo = project_repo

    # ── tenants ───────────────────────────────────────────────────────────────

    async def create_tenant(self, body: TenantCreate, actor_user_id: uuid.UUID) -> Tenant:
        existing = await self._tenant_repo.find_by_slug(body.slug)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already taken")

        tenant = Tenant(name=body.name, slug=body.slug, default_role=body.default_role)
        await self._tenant_repo.save(tenant)

        member = TenantMember(
            tenant_id=tenant.id,
            user_id=actor_user_id,
            role=MemberRole.owner,
        )
        await member.insert()

        await self._audit_service.log_event(
            tenant.id,
            actor_user_id,
            "tenant.created",
            "tenant",
            tenant.id,
            entity_label=tenant.name,
            summary="created",
        )
        return tenant

    async def list_tenants_for_user(self, user_id: uuid.UUID) -> list[Tenant]:
        return await self._tenant_repo.find_by_user(user_id)

    async def get_tenant_or_404(self, tenant_id: uuid.UUID) -> Tenant:
        tenant = await self._tenant_repo.find_by_id(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        return tenant

    async def get_workspace_navigation(self, user_id: uuid.UUID) -> WorkspaceNavigationResponse:
        memberships = await self._tenant_repo.find_memberships_for_user(user_id)
        if not memberships:
            return WorkspaceNavigationResponse(tenants=[])

        membership_by_tenant_id = {membership.tenant_id: membership for membership in memberships}
        tenant_ids = list(membership_by_tenant_id)
        tenants = await self._tenant_repo.find_by_ids(tenant_ids)
        projects = await self._project_repo.find_by_tenant_ids(tenant_ids)

        projects_by_tenant_id: dict[uuid.UUID, list[WorkspaceNavigationProject]] = {
            tenant_id: [] for tenant_id in tenant_ids
        }
        for project in sorted(
            projects,
            key=lambda item: (item.archived_at is not None, item.name.casefold(), item.slug),
        ):
            projects_by_tenant_id.setdefault(project.tenant_id, []).append(
                WorkspaceNavigationProject(
                    id=project.id,
                    name=project.name,
                    slug=project.slug,
                    archived_at=project.archived_at,
                )
            )

        navigation_tenants: list[WorkspaceNavigationTenant] = []
        for tenant in sorted(tenants, key=lambda item: (item.name.casefold(), item.slug)):
            membership = membership_by_tenant_id[tenant.id]
            navigation_tenants.append(
                WorkspaceNavigationTenant(
                    id=tenant.id,
                    name=tenant.name,
                    slug=tenant.slug,
                    role=membership.role,
                    can_create_project=membership.role
                    in {MemberRole.owner, MemberRole.admin, MemberRole.member},
                    projects=projects_by_tenant_id.get(tenant.id, []),
                )
            )

        return WorkspaceNavigationResponse(tenants=navigation_tenants)

    async def update_tenant(
        self, tenant_id: uuid.UUID, body: TenantUpdate, actor_user_id: uuid.UUID
    ) -> Tenant:
        tenant = await self.get_tenant_or_404(tenant_id)

        updates: dict[Any, Any] = {}
        if body.name is not None:
            updates[Tenant.name] = body.name
        if body.default_role is not None:
            updates[Tenant.default_role] = body.default_role

        if updates:
            await tenant.set(updates)

        await self._audit_service.log_event(
            tenant.id,
            actor_user_id,
            "tenant.updated",
            "tenant",
            tenant.id,
            entity_label=tenant.name,
            summary="updated",
        )
        # Reload after update
        reloaded = await self._tenant_repo.find_by_id(tenant_id)
        assert reloaded is not None, "tenant vanished during update"
        return reloaded

    # ── members ───────────────────────────────────────────────────────────────

    async def list_members(self, tenant_id: uuid.UUID) -> list[tuple[TenantMember, User]]:
        return await self._tenant_repo.find_members_with_users(tenant_id)

    async def remove_member(
        self,
        tenant_id: uuid.UUID,
        target_user_id: uuid.UUID,
        actor_user_id: uuid.UUID,
    ) -> None:
        target = await self._tenant_repo.find_member(tenant_id, target_user_id)
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        if target.role == MemberRole.owner and actor_user_id != target_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot remove owner")

        await self._tenant_repo.delete(target)

        removed_user = await self._user_repo.find_by_id(target_user_id)
        removed_label = (
            removed_user.display_name if removed_user is not None else str(target_user_id)
        )

        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            "member.removed",
            "tenant_member",
            target.id,
            entity_label=removed_label,
            summary=f"member removed: {removed_label}",
            details={"removed_user_id": str(target_user_id)},
        )

    # ── invitations ───────────────────────────────────────────────────────────

    async def invite_member(
        self,
        tenant_id: uuid.UUID,
        body: InvitationCreate,
        actor_user_id: uuid.UUID,
    ) -> TenantInvitation:
        """Create an invitation and send the invitation email."""
        tenant = await self.get_tenant_or_404(tenant_id)

        # Check if already a member (by user email)
        existing_user = await self._user_repo.find_by_email(body.email)
        if existing_user is not None:
            member_check = await self._tenant_repo.find_member(tenant_id, existing_user.id)
            if member_check is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="User is already a member"
                )

        invitation = TenantInvitation(
            tenant_id=tenant_id,
            email=body.email,
            role=body.role,
            invited_by=actor_user_id,
            token=secrets.token_urlsafe(32),
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        await invitation.insert()

        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            "invitation.created",
            "invitation",
            invitation.id,
            entity_label=body.email,
            summary=f"invitation created for {body.email} as {body.role.value}",
            details={"email": body.email, "role": body.role.value},
        )

        inviter = await self._user_repo.find_by_id(actor_user_id)
        inviter_name = inviter.display_name if inviter is not None else "A team member"

        await send_tenant_invitation_email(
            recipient_email=body.email,
            tenant_name=tenant.name,
            inviter_name=inviter_name,
            role=body.role.value,
            token=invitation.token,
        )

        return invitation

    async def list_invitations(self, tenant_id: uuid.UUID) -> list[dict[str, Any]]:
        """Invitations sorted by created_at desc, each with its computed status."""
        invitations = await self._tenant_repo.find_invitations(tenant_id)
        invitations = sorted(invitations, key=lambda i: i.created_at, reverse=True)

        return [
            {"invitation": invitation, "status": compute_invitation_status(invitation)}
            for invitation in invitations
        ]

    async def cancel_invitation(
        self, tenant_id: uuid.UUID, invitation_id: uuid.UUID, actor_user_id: uuid.UUID
    ) -> None:
        invitation = await self._tenant_repo.find_invitation_by_id(invitation_id)
        if invitation is None or invitation.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
            )
        if invitation.accepted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation already accepted"
            )
        await invitation.delete()
        await self._audit_service.log_event(
            tenant_id,
            actor_user_id,
            "invitation.cancelled",
            "invitation",
            invitation_id,
            entity_label=invitation.email,
            summary=f"invitation cancelled for {invitation.email}",
            details={"email": invitation.email},
        )

    async def verify_invitation(self, token: str, user_email: str) -> dict[str, Any]:
        invitation = await self._tenant_repo.find_invitation_by_token(token)
        if invitation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
            )

        if invitation.email != user_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invitation is for a different email",
            )

        if invitation.accepted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation already accepted"
            )

        self._ensure_invitation_not_expired(invitation)

        tenant = await self._tenant_repo.find_by_id(invitation.tenant_id)

        return {
            "email": invitation.email,
            "role": invitation.role.value,
            "tenant_name": tenant.name if tenant else "Unknown",
            "expires_at": invitation.expires_at.isoformat(),
        }

    async def accept_invitation(self, token: str, user: User) -> TenantMember:
        invitation = await self._tenant_repo.find_invitation_by_token(token)
        if invitation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
            )

        if invitation.email != user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invitation is for a different email",
            )

        if invitation.accepted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation already accepted"
            )

        self._ensure_invitation_not_expired(invitation)

        # Check not already member
        existing = await self._tenant_repo.find_member(invitation.tenant_id, user.id)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already a member")

        member = TenantMember(
            tenant_id=invitation.tenant_id,
            user_id=user.id,
            role=invitation.role,
            invited_by=invitation.invited_by,
        )
        await member.insert()

        await invitation.set({TenantInvitation.accepted_at: datetime.now(UTC)})

        await self._audit_service.log_event(
            invitation.tenant_id,
            user.id,
            "member.joined",
            "tenant_member",
            member.id,
            entity_label=user.display_name,
            summary=f"{user.email} joined the tenant",
            details={"email": user.email},
        )
        return member

    @staticmethod
    def _ensure_invitation_not_expired(invitation: TenantInvitation) -> None:
        expires_at = invitation.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation expired"
            )
