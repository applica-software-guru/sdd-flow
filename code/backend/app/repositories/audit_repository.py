import re
from datetime import datetime
from typing import Any
from uuid import UUID

from beanie import SortDirection

from app.models.audit_log_entry import AuditLogEntry


class AuditRepository:
    async def create(self, entry: AuditLogEntry) -> AuditLogEntry:
        await entry.insert()
        return entry

    async def find_by_tenant(
        self, tenant_id: UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[AuditLogEntry], int]:
        query = {"tenantId": tenant_id}
        skip = (page - 1) * page_size
        total = await AuditLogEntry.find(query).count()
        items = (
            await AuditLogEntry.find(query)
            .sort([("createdAt", SortDirection.DESCENDING)])
            .skip(skip)
            .limit(page_size)
            .to_list()
        )
        return items, total

    async def find_by_tenant_filtered(
        self,
        tenant_id: UUID,
        action: str | None = None,
        event_type: str | None = None,
        entity_type: str | None = None,
        user_id: UUID | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditLogEntry], int]:
        """Filtered + paginated audit log (mirrors the audit-log endpoint contract)."""
        query: dict[str, Any] = {"tenantId": tenant_id}
        if action is not None:
            query["eventType"] = {"$regex": re.escape(action), "$options": "i"}
        elif event_type is not None:
            query["eventType"] = event_type
        if entity_type is not None:
            query["entityType"] = entity_type
        if user_id is not None:
            query["userId"] = user_id
        if from_dt is not None or to_dt is not None:
            range_query: dict[str, Any] = {}
            if from_dt is not None:
                range_query["$gte"] = from_dt
            if to_dt is not None:
                range_query["$lte"] = to_dt
            query["createdAt"] = range_query

        skip = (page - 1) * page_size
        total = await AuditLogEntry.find(query).count()
        items = (
            await AuditLogEntry.find(query)
            .sort([("createdAt", SortDirection.DESCENDING)])
            .skip(skip)
            .limit(page_size)
            .to_list()
        )
        return items, total

    async def find_by_event_type(
        self, tenant_id: UUID, pattern: Any, limit: int = 10
    ) -> list[AuditLogEntry]:
        """Audit entries whose event type matches `pattern` (a regex).

        Mirrors the global search endpoint: the pattern is passed to MongoDB as
        a regex (same semantics as the previous direct model query).
        """
        return (
            await AuditLogEntry.find({"tenantId": tenant_id, "eventType": pattern})
            .limit(limit)
            .to_list()
        )

    async def search(self, tenant_id: UUID, pattern: Any) -> list[AuditLogEntry]:
        return await AuditLogEntry.find(
            {"tenantId": tenant_id, "eventType": {"$regex": pattern}}
        ).to_list()

    async def delete_by_tenant(self, tenant_id: UUID) -> int:
        result = await AuditLogEntry.find({"tenantId": tenant_id}).delete()
        return result.deleted_count if result else 0
