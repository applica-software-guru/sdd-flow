"""Audit service: append-only audit trail writes and admin queries.

Injected into domain services and controllers via the composition root
(``app/dependencies.py``); it never instantiates its own collaborators.
"""

import math
import uuid
from datetime import datetime
from typing import Any

from app.models.audit_log_entry import AuditLogEntry
from app.repositories import AuditRepository, TenantRepository, UserRepository
from app.schemas.users import UserBrief


class AuditService:
    def __init__(
        self,
        audit_repo: AuditRepository,
        user_repo: UserRepository,
        tenant_repo: TenantRepository,
    ) -> None:
        self._audit_repo = audit_repo
        self._user_repo = user_repo
        self._tenant_repo = tenant_repo

    async def log_event(
        self,
        tenant_id: uuid.UUID | None,
        user_id: uuid.UUID | None,
        event_type: str,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        details: dict[str, Any] | None = None,
        entity_label: str | None = None,
        summary: str | None = None,
    ) -> AuditLogEntry:
        """Append an immutable audit entry.

        `entity_label` and `summary` are denormalized at write time so entries
        stay human-readable even after the target entity is deleted or
        modified.
        """
        entry = AuditLogEntry(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_label=entity_label,
            summary=summary,
            details=details or {},
        )
        return await self._audit_repo.create(entry)

    async def log_event_for_user_tenants(
        self,
        user_id: uuid.UUID,
        event_type: str,
        tenant_ids: list[uuid.UUID] | None = None,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        details: dict[str, Any] | None = None,
        entity_label: str | None = None,
        summary: str | None = None,
    ) -> None:
        """Append an audit entry for each tenant the user belongs to.

        Profile-level events (display name change, password change) are not
        scoped to a single tenant, so they are recorded in every tenant the
        user is a member of to keep the per-tenant audit log complete. When
        `tenant_ids` is omitted, the memberships are resolved here from the
        user id.
        """
        if tenant_ids is None:
            tenant_ids = await self._tenant_repo.find_tenant_ids_for_user(user_id)
        for tenant_id in tenant_ids:
            await self.log_event(
                tenant_id=tenant_id,
                user_id=user_id,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                entity_label=entity_label,
                summary=summary,
                details=details or {},
            )

    async def query_audit_log(
        self,
        tenant_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50,
        action: str | None = None,
        event_type: str | None = None,
        entity_type: str | None = None,
        user_id: uuid.UUID | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> tuple[list[tuple[AuditLogEntry, UserBrief | None]], int, int]:
        """Filtered + paginated audit log with batched user briefs (no N+1).

        Returns (items as (entry, user_brief) pairs, total, pages).
        """
        items, total = await self._audit_repo.find_by_tenant_filtered(
            tenant_id,
            action=action,
            event_type=event_type,
            entity_type=entity_type,
            user_id=user_id,
            from_dt=from_dt,
            to_dt=to_dt,
            page=page,
            page_size=page_size,
        )

        # Batch-resolve users for the current page (single query, avoids N+1)
        user_ids = {i.user_id for i in items if i.user_id is not None}
        users_by_id: dict[uuid.UUID, UserBrief] = {}
        if user_ids:
            users = await self._user_repo.find_by_ids(list(user_ids))
            users_by_id = {
                u.id: UserBrief(
                    id=u.id,
                    display_name=u.display_name,
                    email=u.email,
                    avatar_url=u.avatar_url,
                )
                for u in users
            }

        pairs = [(i, users_by_id.get(i.user_id) if i.user_id is not None else None) for i in items]
        pages = math.ceil(total / page_size) if total > 0 else 0
        return pairs, total, pages
