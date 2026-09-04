import enum
from uuid import UUID

from pydantic import Field
from pymongo import IndexModel

from app.models.base import ImmutableDocument


class MessageKind(enum.StrEnum):
    output = "output"
    question = "question"
    answer = "answer"


class WorkerJobMessage(ImmutableDocument):
    job_id: UUID = Field()
    kind: MessageKind
    content: str
    sequence: int = 0

    class Settings:
        name = "worker_job_messages"
        indexes = [
            IndexModel([("jobId", 1), ("sequence", 1)]),
        ]
