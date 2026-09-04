import enum
from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.models.base import BaseDocument


class EntityType(enum.StrEnum):
    change_request = "change_request"
    bug = "bug"


class Comment(BaseDocument):
    entity_type: EntityType = Field()
    entity_id: UUID = Field()
    author_id: UUID = Field()
    body: str

    class Settings:
        name = "comments"
        indexes = [
            IndexModel("entityId"),
            IndexModel([("entityType", 1), ("entityId", 1)]),
        ]
