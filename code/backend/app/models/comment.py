import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin


class EntityType(str, enum.Enum):
    change_request = "change_request"
    bug = "bug"


class Comment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "comments"

    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType, name="comment_entity_type_enum"), nullable=False
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)

    author: Mapped["User"] = relationship("User", foreign_keys=[author_id])
