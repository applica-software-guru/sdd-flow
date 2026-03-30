from beanie import Document, before_event, Replace, Update, Insert
from pydantic import ConfigDict, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BaseDocument(Document):
    model_config = ConfigDict(populate_by_name=True)
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=utcnow, alias="createdAt")
    updated_at: datetime = Field(default_factory=utcnow, alias="updatedAt")

    @before_event(Replace, Update)
    def _set_updated_at(self):
        self.updated_at = utcnow()


class ImmutableDocument(Document):
    model_config = ConfigDict(populate_by_name=True)
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=utcnow, alias="createdAt")
