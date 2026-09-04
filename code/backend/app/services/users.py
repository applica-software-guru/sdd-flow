import uuid

from fastapi import HTTPException, status

from app.models.tenant_member import TenantMember
from app.models.user import User
from app.schemas.users import UserBrief


async def ensure_tenant_member(tenant_id: uuid.UUID, user_id: uuid.UUID) -> TenantMember:
    """Raise 404 if the user is not an active member of the tenant."""
    member = await TenantMember.find_one(
        {"tenantId": tenant_id, "userId": user_id}
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignee is not a member of this tenant",
        )
    return member


async def resolve_user_briefs(user_ids: list[uuid.UUID] | set[uuid.UUID]) -> dict[uuid.UUID, UserBrief]:
    """Batch-resolve users into UserBrief objects (single query, no N+1)."""
    ids = [u for u in set(user_ids) if u is not None]
    if not ids:
        return {}
    users = await User.find({"_id": {"$in": ids}}).to_list()
    return {
        u.id: UserBrief(id=u.id, display_name=u.display_name, email=u.email)
        for u in users
    }


async def resolve_user_brief(user_id: uuid.UUID | None) -> UserBrief | None:
    if user_id is None:
        return None
    users = await resolve_user_briefs([user_id])
    return users.get(user_id)
