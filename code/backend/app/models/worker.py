import enum
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.models.base import BaseDocument, utcnow


class WorkerStatus(enum.StrEnum):
    online = "online"
    offline = "offline"
    busy = "busy"


class Worker(BaseDocument):
    project_id: UUID = Field()
    name: str
    status: WorkerStatus = WorkerStatus.offline
    agent: str = "claude"
    branch: str | None = None
    last_heartbeat_at: datetime = Field(default_factory=utcnow)
    registered_at: datetime = Field(default_factory=utcnow)
    metadata_: dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "workers"
        indexes = [
            IndexModel([("projectId", 1), ("name", 1)], unique=True),
        ]
