from uuid import UUID

from beanie import SortDirection

from app.models.assignment_history import AssignmentHistory


class AssignmentRepository:
    async def create(self, entry: AssignmentHistory) -> AssignmentHistory:
        await entry.insert()
        return entry

    async def find_by_entity(self, entity_type: str, entity_id: UUID) -> list[AssignmentHistory]:
        return (
            await AssignmentHistory.find({"entityType": entity_type, "entityId": entity_id})
            .sort([("createdAt", SortDirection.DESCENDING)])
            .to_list()
        )
