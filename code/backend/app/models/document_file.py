import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin


class DocStatus(str, enum.Enum):
    draft = "draft"
    new = "new"
    changed = "changed"
    synced = "synced"
    deleted = "deleted"


class DocumentFile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "document_files"
    __table_args__ = (
        UniqueConstraint("project_id", "path", name="uq_doc_project_path"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[DocStatus] = mapped_column(
        Enum(DocStatus, name="doc_status_enum"), default=DocStatus.new, nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    last_modified_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    project: Mapped["Project"] = relationship("Project", back_populates="documents")
    modifier: Mapped["User | None"] = relationship("User", foreign_keys=[last_modified_by])
