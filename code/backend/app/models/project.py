from typing import Optional
from datetime import datetime
from pymongo import IndexModel
from pydantic import Field
from uuid import UUID

from app.models.base import BaseDocument


class Project(BaseDocument):
    tenant_id: UUID = Field(alias="tenantId")
    name: str
    slug: str
    description: Optional[str] = None
    archived_at: Optional[datetime] = Field(default=None, alias="archivedAt")

    class Settings:
        name = "projects"
        indexes = [
            IndexModel([("tenantId", 1), ("slug", 1)], unique=True),
        ]
