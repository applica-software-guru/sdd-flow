from typing import Optional
from uuid import UUID

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
            .sort([("createdAt", -1)])
            .skip(skip)
            .limit(page_size)
            .to_list()
        )
        return items, total

    async def search(self, tenant_id: UUID, pattern) -> list[AuditLogEntry]:
        return await AuditLogEntry.find(
            {"tenantId": tenant_id, "eventType": {"$regex": pattern}}
        ).to_list()

    async def delete_by_tenant(self, tenant_id: UUID) -> int:
        result = await AuditLogEntry.find({"tenantId": tenant_id}).delete()
        return result.deleted_count if result else 0
