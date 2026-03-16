import enum

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin


class DefaultRole(str, enum.Enum):
    member = "member"
    viewer = "viewer"


class Tenant(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    default_role: Mapped[DefaultRole] = mapped_column(
        Enum(DefaultRole, name="default_role_enum"),
        default=DefaultRole.member,
        nullable=False,
    )

    members: Mapped[list["TenantMember"]] = relationship(
        "TenantMember", back_populates="tenant"
    )
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="tenant")
    invitations: Mapped[list["TenantInvitation"]] = relationship(
        "TenantInvitation", back_populates="tenant"
    )
