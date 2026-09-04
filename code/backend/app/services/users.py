"""User service: membership checks and batched user briefs."""

import uuid
from collections.abc import Iterable

from fastapi import HTTPException, status

from app.models.tenant_member import TenantMember
from app.repositories import TenantRepository, UserRepository
from app.schemas.users import UserBrief


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        tenant_repo: TenantRepository,
    ) -> None:
        self._user_repo = user_repo
        self._tenant_repo = tenant_repo

    async def ensure_tenant_member(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> TenantMember:
        """Return the membership or raise 404 if the user is not an active member."""
        member = await self._tenant_repo.find_member(tenant_id, user_id)
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee is not a member of this tenant",
            )
        return member

    async def resolve_user_briefs(
        self, user_ids: Iterable[uuid.UUID | None]
    ) -> dict[uuid.UUID, UserBrief]:
        """Batch-resolve users into UserBrief objects (single query, no N+1)."""
        ids = [u for u in set(user_ids) if u is not None]
        if not ids:
            return {}
        users = await self._user_repo.find_by_ids(ids)
        return {u.id: UserBrief(id=u.id, display_name=u.display_name, email=u.email) for u in users}

    async def resolve_user_brief(self, user_id: uuid.UUID | None) -> UserBrief | None:
        if user_id is None:
            return None
        users = await self.resolve_user_briefs([user_id])
        return users.get(user_id)
