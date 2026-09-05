from uuid import UUID

from app.models.tenant import Tenant
from app.models.tenant_invitation import TenantInvitation
from app.models.tenant_member import TenantMember
from app.models.user import User
from app.utils.bson import uuid_to_bin


class TenantRepository:
    """Repository for the tenant aggregate: tenants, members and invitations.

    Unlike the other repositories it manages three Beanie documents, so it
    does not inherit the single-aggregate BaseRepository.
    """

    async def find_by_id(self, id: UUID) -> Tenant | None:
        return await Tenant.get(id)

    async def find_by_slug(self, slug: str) -> Tenant | None:
        return await Tenant.find_one(Tenant.slug == slug)

    async def find_by_user(self, user_id: UUID) -> list[Tenant]:
        memberships = await self.find_memberships_for_user(user_id)
        tenant_ids = [m.tenant_id for m in memberships]
        return await self.find_by_ids(tenant_ids)

    async def find_by_ids(self, tenant_ids: list[UUID]) -> list[Tenant]:
        if not tenant_ids:
            return []
        tenant_id_bins = [uuid_to_bin(tid) for tid in tenant_ids]
        return await Tenant.find({"_id": {"$in": tenant_id_bins}}).to_list()

    async def find_memberships_for_user(self, user_id: UUID) -> list[TenantMember]:
        return await TenantMember.find({"userId": user_id}).to_list()

    async def find_member(self, tenant_id: UUID, user_id: UUID) -> TenantMember | None:
        return await TenantMember.find_one({"tenantId": tenant_id, "userId": user_id})

    async def find_member_user_ids(self, tenant_id: UUID) -> list[UUID]:
        """All member user ids of a tenant (any role)."""
        members = await TenantMember.find({"tenantId": tenant_id}).to_list()
        return [m.user_id for m in members]

    async def find_tenant_ids_for_user(self, user_id: UUID) -> list[UUID]:
        """Ids of the tenants the user is a member of."""
        memberships = await TenantMember.find({"userId": user_id}).to_list()
        return [m.tenant_id for m in memberships]

    async def find_members_with_users(self, tenant_id: UUID) -> list[tuple[TenantMember, User]]:
        members = await TenantMember.find({"tenantId": tenant_id}).to_list()
        user_ids = [m.user_id for m in members]
        if not user_ids:
            return []
        user_id_bins = [uuid_to_bin(uid) for uid in user_ids]
        users = await User.find({"_id": {"$in": user_id_bins}}).to_list()
        user_map = {u.id: u for u in users}
        return [(m, user_map[m.user_id]) for m in members if m.user_id in user_map]

    async def find_invitations(self, tenant_id: UUID) -> list[TenantInvitation]:
        return await TenantInvitation.find({"tenantId": tenant_id}).to_list()

    async def find_invitation_by_token(self, token: str) -> TenantInvitation | None:
        return await TenantInvitation.find_one(TenantInvitation.token == token)

    async def find_invitation_by_id(self, invitation_id: UUID) -> TenantInvitation | None:
        return await TenantInvitation.get(invitation_id)

    async def save(
        self, doc: Tenant | TenantMember | TenantInvitation
    ) -> Tenant | TenantMember | TenantInvitation:
        """Save one of the tenant-aggregate documents (tenant, member, invitation)."""
        await doc.save()
        return doc

    async def delete(self, doc: Tenant | TenantMember | TenantInvitation) -> None:
        await doc.delete()
