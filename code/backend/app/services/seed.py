import secrets
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import DefaultRole, Tenant
from app.models.tenant_member import MemberRole, TenantMember
from app.models.user import User
from app.services.auth import hash_password


async def seed_admin_user(db: AsyncSession) -> None:
    """Create a default admin user, tenant, and membership on first startup.

    Skips silently if any user already exists.
    """
    result = await db.execute(select(func.count()).select_from(User))
    count = result.scalar_one()
    if count > 0:
        return

    password = secrets.token_urlsafe(16)

    user = User(
        email="admin@sddflow.dev",
        display_name="Admin",
        password_hash=hash_password(password),
        email_verified=True,
    )
    db.add(user)
    await db.flush()

    tenant = Tenant(
        name="Default",
        slug="default",
        default_role=DefaultRole.member,
    )
    db.add(tenant)
    await db.flush()

    membership = TenantMember(
        tenant_id=tenant.id,
        user_id=user.id,
        role=MemberRole.owner,
        joined_at=datetime.now(timezone.utc),
    )
    db.add(membership)
    await db.commit()

    print("")
    print("============================================")
    print("  SDD Flow — First Run Setup")
    print("============================================")
    print("  Admin account created:")
    print(f"    Email:    {user.email}")
    print(f"    Password: {password}")
    print("")
    print(f'  Default tenant: "{tenant.name}"')
    print("")
    print("  ⚠ Change this password after first login!")
    print("============================================")
    print("")
