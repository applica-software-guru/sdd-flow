import enum
from typing import Optional
from pymongo import IndexModel
from pydantic import Field
from uuid import UUID

from app.models.base import BaseDocument


class DocStatus(str, enum.Enum):
    draft = "draft"
    new = "new"
    changed = "changed"
    synced = "synced"
    deleted = "deleted"


class DocumentFile(BaseDocument):
    project_id: UUID = Field(alias="projectId")
    path: str
    title: str
    status: DocStatus = DocStatus.new
    version: int = 1
    content: str = ""
    last_modified_by: Optional[UUID] = Field(default=None, alias="lastModifiedBy")

    class Settings:
        name = "document_files"
        indexes = [
            IndexModel([("projectId", 1), ("path", 1)], unique=True),
        ]
