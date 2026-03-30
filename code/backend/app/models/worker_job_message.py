import enum
from pymongo import IndexModel
from pydantic import Field
from uuid import UUID

from app.models.base import ImmutableDocument


class MessageKind(str, enum.Enum):
    output = "output"
    question = "question"
    answer = "answer"


class WorkerJobMessage(ImmutableDocument):
    job_id: UUID = Field(alias="jobId")
    kind: MessageKind
    content: str
    sequence: int = 0

    class Settings:
        name = "worker_job_messages"
        indexes = [
            IndexModel([("jobId", 1), ("sequence", 1)]),
        ]
