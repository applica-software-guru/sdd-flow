"""Application service for read-only global platform administration."""

import math
from datetime import datetime
from typing import Any
from uuid import UUID

from app.models.user import PlatformRole, User
from app.repositories.platform_admin_repository import PlatformAdminRepository
from app.services.audit import AuditService


class PlatformAdminService:
    def __init__(self, repository: PlatformAdminRepository, audit_service: AuditService) -> None:
        self._repository = repository
        self._audit = audit_service

    @staticmethod
    def _page(items: list[dict[str, Any]], total: int, page: int, page_size: int) -> dict[str, Any]:
        return {
            "items": items,
            "total": total,
            "page": page,
            "pages": math.ceil(total / page_size) if total else 0,
        }

    async def _record_view(self, user: User, event_type: str) -> None:
        await self._audit.log_event(
            tenant_id=None,
            user_id=user.id,
            event_type=event_type,
            entity_type="platform_admin",
            details={},
        )

    async def overview(self, user: User) -> dict[str, Any]:
        users_count, tenants_count, projects_count = await self._repository.count_inventory()
        recent = await self._repository.recent_events()
        result: dict[str, Any] = {
            "users_count": users_count,
            "tenants_count": tenants_count,
            "projects_count": projects_count,
            "recent_login_count": await self._repository.count_event("auth.login_success"),
            "recent_failed_login_count": await self._repository.count_event("auth.login_failed"),
            "recent_events": [
                {"id": str(item.id), "event_type": item.event_type, "created_at": item.created_at}
                for item in recent
            ],
        }
        await self._record_view(user, "super_user.admin_view_opened")
        return result

    async def users(
        self,
        user: User,
        *,
        page: int,
        page_size: int,
        search: str | None,
        platform_role: PlatformRole | None,
        email_verified: bool | None,
    ) -> dict[str, Any]:
        records, total = await self._repository.list_users(
            page=page,
            page_size=page_size,
            search=search,
            platform_role=platform_role,
            email_verified=email_verified,
        )
        membership_counts = await self._repository.membership_counts(
            [record.id for record in records]
        )
        items: list[dict[str, Any]] = []
        for record in records:
            items.append(
                {
                    "id": str(record.id),
                    "email": record.email,
                    "display_name": record.display_name,
                    "platform_role": record.platform_role.value,
                    "email_verified": record.email_verified,
                    "google_linked": record.google_linked,
                    "has_password": record.has_password,
                    "tenant_count": membership_counts.get(record.id, 0),
                    "created_at": record.created_at,
                    "updated_at": record.updated_at,
                }
            )
        await self._record_view(user, "super_user.admin_users_viewed")
        return self._page(items, total, page, page_size)

    async def tenants(
        self, user: User, *, page: int, page_size: int, search: str | None
    ) -> dict[str, Any]:
        records, total = await self._repository.list_tenants(
            page=page, page_size=page_size, search=search
        )
        member_counts, project_counts = await self._repository.tenant_inventory_counts(
            [record.id for record in records]
        )
        items: list[dict[str, Any]] = []
        for record in records:
            items.append(
                {
                    "id": str(record.id),
                    "name": record.name,
                    "slug": record.slug,
                    "member_count": member_counts.get(record.id, 0),
                    "project_count": project_counts.get(record.id, 0),
                    "created_at": record.created_at,
                    "updated_at": record.updated_at,
                }
            )
        await self._record_view(user, "super_user.admin_tenants_viewed")
        return self._page(items, total, page, page_size)

    async def projects(
        self,
        user: User,
        *,
        page: int,
        page_size: int,
        search: str | None,
        tenant_id: UUID | None,
        archived: bool | None,
    ) -> dict[str, Any]:
        records, total = await self._repository.list_projects(
            page=page,
            page_size=page_size,
            search=search,
            tenant_id=tenant_id,
            archived=archived,
        )
        tenants = await self._repository.tenants_by_ids({record.tenant_id for record in records})
        items: list[dict[str, Any]] = [
            {
                "id": str(record.id),
                "tenant_id": str(record.tenant_id),
                "tenant_name": tenants[record.tenant_id].name
                if record.tenant_id in tenants
                else "Unknown tenant",
                "name": record.name,
                "slug": record.slug,
                "archived_at": record.archived_at,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
            }
            for record in records
        ]
        await self._record_view(user, "super_user.admin_projects_viewed")
        return self._page(items, total, page, page_size)

    async def audit_log(
        self,
        user: User,
        *,
        page: int,
        page_size: int,
        event_type: str | None,
        user_id: UUID | None,
        tenant_id: UUID | None,
        project_id: UUID | None,
        from_dt: datetime | None,
        to_dt: datetime | None,
    ) -> dict[str, Any]:
        records, total = await self._repository.list_audit(
            page=page,
            page_size=page_size,
            event_type=event_type,
            user_id=user_id,
            tenant_id=tenant_id,
            project_id=project_id,
            from_dt=from_dt,
            to_dt=to_dt,
        )
        items: list[dict[str, Any]] = [
            {
                "id": str(record.id),
                "tenant_id": str(record.tenant_id) if record.tenant_id else None,
                "user_id": str(record.user_id) if record.user_id else None,
                "event_type": record.event_type,
                "entity_type": record.entity_type,
                "entity_id": str(record.entity_id) if record.entity_id else None,
                "summary": record.summary,
                "details": record.details,
                "created_at": record.created_at,
            }
            for record in records
        ]
        await self._record_view(user, "super_user.admin_audit_viewed")
        return self._page(items, total, page, page_size)
