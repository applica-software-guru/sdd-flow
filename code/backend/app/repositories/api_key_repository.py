from uuid import UUID

from beanie import SortDirection

from app.models.api_key import ApiKey
from app.repositories.base import BaseRepository


class ApiKeyRepository(BaseRepository[ApiKey]):
    model = ApiKey

    async def find_by_id(self, id: UUID) -> ApiKey | None:
        return await ApiKey.get(id)

    async def find_by_project(self, project_id: UUID) -> list[ApiKey]:
        return (
            await ApiKey.find({"projectId": project_id})
            .sort([("createdAt", SortDirection.DESCENDING)])
            .to_list()
        )

    async def create(self, doc: ApiKey) -> ApiKey:
        await doc.insert()
        return doc

    async def save(self, doc: ApiKey) -> ApiKey:
        await doc.save()
        return doc
