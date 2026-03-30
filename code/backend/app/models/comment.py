import enum
from pymongo import IndexModel
from pydantic import Field
from uuid import UUID

from app.models.base import BaseDocument


class EntityType(str, enum.Enum):
    change_request = "change_request"
    bug = "bug"


class Comment(BaseDocument):
    entity_type: EntityType = Field(alias="entityType")
    entity_id: UUID = Field(alias="entityId")
    author_id: UUID = Field(alias="authorId")
    body: str

    class Settings:
        name = "comments"
        indexes = [
            IndexModel("entityId"),
            IndexModel([("entityType", 1), ("entityId", 1)]),
        ]
