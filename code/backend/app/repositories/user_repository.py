from uuid import UUID

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def find_by_email(self, email: str) -> User | None:
        return await User.find_one(User.email == email)

    async def find_by_google_id(self, google_id: str) -> User | None:
        return await User.find_one({"googleId": google_id})

    async def find_by_id(self, id: UUID) -> User | None:
        return await User.get(str(id))

    async def find_by_ids(self, ids: list[UUID]) -> list[User]:
        return await User.find({"_id": {"$in": list(set(ids))}}).to_list()

    async def save(self, doc: User) -> User:
        await doc.save()
        return doc
