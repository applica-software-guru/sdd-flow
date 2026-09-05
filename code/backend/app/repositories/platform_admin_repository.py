"""Global read-only queries used by platform administration."""

import re
from datetime import datetime
from typing import Any
from uuid import UUID

from beanie import SortDirection

from app.models.audit_log_entry import AuditLogEntry
from app.models.project import Project
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.user import PlatformRole, User
from app.utils.bson import bin_to_uuid, uuid_to_bin
from app.utils.mongo import raw_collection


class PlatformAdminRepository:
    async def count_inventory(self) -> tuple[int, int, int]:
        return (
            await User.find_all().count(),
            await Tenant.find_all().count(),
            await Project.find_all().count(),
        )

    async def count_event(self, event_type: str) -> int:
        return await AuditLogEntry.find({"eventType": event_type}).count()

    async def recent_events(self, limit: int = 10) -> list[AuditLogEntry]:
        return (
            await AuditLogEntry.find_all()
            .sort([("createdAt", SortDirection.DESCENDING)])
            .limit(limit)
            .to_list()
        )

    async def list_users(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        platform_role: PlatformRole | None,
        email_verified: bool | None,
    ) -> tuple[list[User], int]:
        query: dict[str, Any] = {}
        if search:
            pattern = {"$regex": re.escape(search), "$options": "i"}
            query["$or"] = [{"email": pattern}, {"displayName": pattern}]
        if platform_role is not None:
            query["platformRole"] = platform_role.value
        if email_verified is not None:
            query["emailVerified"] = email_verified
        total = await User.find(query).count()
        records = (
            await User.find(query)
            .sort("email")
            .skip((page - 1) * page_size)
            .limit(page_size)
            .to_list()
        )
        return records, total

    async def membership_counts(self, user_ids: list[UUID]) -> dict[UUID, int]:
        if not user_ids:
            return {}
        pipeline: list[dict[str, Any]] = [
            {"$match": {"userId": {"$in": [uuid_to_bin(item) for item in user_ids]}}},
            {"$group": {"_id": "$userId", "count": {"$sum": 1}}},
        ]
        result: dict[UUID, int] = {}
        async for row in await raw_collection(TenantMember).aggregate(pipeline):
            user_id = bin_to_uuid(row["_id"])
            if user_id is not None:
                result[user_id] = int(row["count"])
        return result

    async def list_tenants(
        self, *, page: int, page_size: int, search: str | None
    ) -> tuple[list[Tenant], int]:
        query: dict[str, Any] = {}
        if search:
            pattern = {"$regex": re.escape(search), "$options": "i"}
            query["$or"] = [{"name": pattern}, {"slug": pattern}]
        total = await Tenant.find(query).count()
        records = (
            await Tenant.find(query)
            .sort("name")
            .skip((page - 1) * page_size)
            .limit(page_size)
            .to_list()
        )
        return records, total

    async def tenant_inventory_counts(
        self, tenant_ids: list[UUID]
    ) -> tuple[dict[UUID, int], dict[UUID, int]]:
        if not tenant_ids:
            return {}, {}
        ids = [uuid_to_bin(item) for item in tenant_ids]
        pipeline: list[dict[str, Any]] = [
            {"$match": {"tenantId": {"$in": ids}}},
            {"$group": {"_id": "$tenantId", "count": {"$sum": 1}}},
        ]
        member_counts: dict[UUID, int] = {}
        project_counts: dict[UUID, int] = {}
        async for row in await raw_collection(TenantMember).aggregate(pipeline):
            tenant_id = bin_to_uuid(row["_id"])
            if tenant_id is not None:
                member_counts[tenant_id] = int(row["count"])
        async for row in await raw_collection(Project).aggregate(pipeline):
            tenant_id = bin_to_uuid(row["_id"])
            if tenant_id is not None:
                project_counts[tenant_id] = int(row["count"])
        return member_counts, project_counts

    async def list_projects(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        tenant_id: UUID | None,
        archived: bool | None,
    ) -> tuple[list[Project], int]:
        query: dict[str, Any] = {}
        if search:
            pattern = {"$regex": re.escape(search), "$options": "i"}
            query["$or"] = [{"name": pattern}, {"slug": pattern}]
        if tenant_id is not None:
            query["tenantId"] = tenant_id
        if archived is not None:
            query["archivedAt"] = {"$ne": None} if archived else None
        total = await Project.find(query).count()
        records = (
            await Project.find(query)
            .sort("name")
            .skip((page - 1) * page_size)
            .limit(page_size)
            .to_list()
        )
        return records, total

    async def tenants_by_ids(self, tenant_ids: set[UUID]) -> dict[UUID, Tenant]:
        if not tenant_ids:
            return {}
        ids = [uuid_to_bin(tenant_id) for tenant_id in tenant_ids]
        tenants = await Tenant.find({"_id": {"$in": ids}}).to_list()
        return {tenant.id: tenant for tenant in tenants}

    async def list_audit(
        self,
        *,
        page: int,
        page_size: int,
        event_type: str | None,
        user_id: UUID | None,
        tenant_id: UUID | None,
        project_id: UUID | None,
        from_dt: datetime | None,
        to_dt: datetime | None,
    ) -> tuple[list[AuditLogEntry], int]:
        query: dict[str, Any] = {}
        if event_type:
            query["eventType"] = event_type
        if user_id:
            query["userId"] = user_id
        if tenant_id:
            query["tenantId"] = tenant_id
        if project_id:
            query["details.project_id"] = str(project_id)
        if from_dt or to_dt:
            query["createdAt"] = {
                **({"$gte": from_dt} if from_dt else {}),
                **({"$lte": to_dt} if to_dt else {}),
            }
        total = await AuditLogEntry.find(query).count()
        records = (
            await AuditLogEntry.find(query)
            .sort([("createdAt", SortDirection.DESCENDING)])
            .skip((page - 1) * page_size)
            .limit(page_size)
            .to_list()
        )
        return records, total
