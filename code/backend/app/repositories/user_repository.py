from typing import Optional
from uuid import UUID

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def find_by_email(self, email: str) -> Optional[User]:
        return await User.find_one(User.email == email)

    async def find_by_google_id(self, google_id: str) -> Optional[User]:
        return await User.find_one({"googleId": google_id})

    async def find_by_id(self, id: UUID) -> Optional[User]:
        return await User.get(str(id))

    async def save(self, user: User) -> User:
        await user.save()
        return user
