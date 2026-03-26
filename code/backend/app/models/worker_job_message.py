import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin


class MessageKind(str, enum.Enum):
    output = "output"
    question = "question"
    answer = "answer"


class WorkerJobMessage(UUIDMixin, Base):
    __tablename__ = "worker_job_messages"
    __table_args__ = (
        Index("ix_worker_job_messages_job_sequence", "job_id", "sequence"),
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worker_jobs.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[MessageKind] = mapped_column(
        Enum(MessageKind, name="message_kind_enum"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    job: Mapped["WorkerJob"] = relationship("WorkerJob", back_populates="messages")
