import enum
from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.models.base import BaseDocument


class DocStatus(enum.StrEnum):
    draft = "draft"
    new = "new"
    changed = "changed"
    synced = "synced"
    deleted = "deleted"


class DocumentFile(BaseDocument):
    project_id: UUID = Field()
    path: str
    title: str
    status: DocStatus = DocStatus.new
    version: int = 1
    content: str = ""
    last_modified_by: UUID | None = Field(default=None)

    class Settings:
        name = "document_files"
        indexes = [
            IndexModel([("projectId", 1), ("path", 1)], unique=True),
        ]
