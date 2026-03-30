from typing import Generic, TypeVar, Optional
from uuid import UUID
from beanie import Document

T = TypeVar("T", bound=Document)


class BaseRepository(Generic[T]):
    model: type[T]

    async def find_by_id(self, id: UUID) -> Optional[T]:
        return await self.model.get(str(id))

    async def save(self, doc: T) -> T:
        await doc.save()
        return doc

    async def delete(self, doc: T) -> None:
        await doc.delete()
