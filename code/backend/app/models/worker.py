import enum
from typing import Optional
from datetime import datetime
from pymongo import IndexModel
from pydantic import Field
from uuid import UUID

from app.models.base import BaseDocument, utcnow


class WorkerStatus(str, enum.Enum):
    online = "online"
    offline = "offline"
    busy = "busy"


class Worker(BaseDocument):
    project_id: UUID = Field(alias="projectId")
    name: str
    status: WorkerStatus = WorkerStatus.offline
    agent: str = "claude"
    branch: Optional[str] = None
    last_heartbeat_at: datetime = Field(default_factory=utcnow, alias="lastHeartbeatAt")
    registered_at: datetime = Field(default_factory=utcnow, alias="registeredAt")
    metadata_: dict = Field(default_factory=dict, alias="metadata")

    class Settings:
        name = "workers"
        indexes = [
            IndexModel([("projectId", 1), ("name", 1)], unique=True),
        ]
