from datetime import datetime
from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.models.base import BaseDocument


class Project(BaseDocument):
    tenant_id: UUID = Field()
    name: str
    slug: str
    description: str | None = None
    archived_at: datetime | None = Field(default=None)

    class Settings:
        name = "projects"
        indexes = [
            IndexModel([("tenantId", 1), ("slug", 1)], unique=True),
        ]
