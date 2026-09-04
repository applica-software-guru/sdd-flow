import uuid

from pydantic import BaseModel


class UserBrief(BaseModel):
    """Lightweight resolved user info embedded in API responses."""

    id: uuid.UUID
    display_name: str
    email: str
