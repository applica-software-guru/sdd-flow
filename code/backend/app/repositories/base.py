from uuid import UUID

from beanie import Document


class BaseRepository[T: Document]:
    model: type[T]

    async def find_by_id(self, id: UUID) -> T | None:
        return await self.model.get(str(id))

    async def save(self, doc: T) -> T:
        await doc.save()
        return doc

    async def delete(self, doc: T) -> None:
        await doc.delete()
