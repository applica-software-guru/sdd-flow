from datetime import UTC, datetime
from uuid import UUID, uuid4

from beanie import Document, Replace, Update, before_event
from pydantic import ConfigDict, Field, alias_generators


def utcnow() -> datetime:
    return datetime.now(UTC)


def bson_alias(s: str) -> str:
    """MongoDB storage alias: snake_case field -> camelCase key, id -> _id.

    Equivalent to Beanie's built-in `document_alias_generator` plus camelCase,
    so stored keys stay `projectId`/`createdAt`/... as before. Declared here so
    type checkers synthesize `__init__` parameters from the snake_case field
    names (Beanie's own alias_generator opaque to pyright makes it derive
    constructor params from explicit aliases instead).
    """
    if s == "id":
        return "_id"
    return alias_generators.to_camel(s)


class BaseDocument(Document):
    model_config = ConfigDict(populate_by_name=True, alias_generator=bson_alias)
    # Deliberate override: this app stores string UUIDs as MongoDB `_id`
    # (see system/architecture.md), not Beanie's default ObjectId.
    id: UUID = Field(default_factory=uuid4)  # pyright: ignore[reportIncompatibleVariableOverride]
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @before_event(Replace, Update)
    def _set_updated_at(self):
        self.updated_at = utcnow()


class ImmutableDocument(Document):
    model_config = ConfigDict(populate_by_name=True, alias_generator=bson_alias)
    # Deliberate override: string UUID `_id` instead of Beanie's ObjectId (see BaseDocument).
    id: UUID = Field(default_factory=uuid4)  # pyright: ignore[reportIncompatibleVariableOverride]
    created_at: datetime = Field(default_factory=utcnow)
