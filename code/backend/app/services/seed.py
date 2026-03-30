import secrets

from pymongo.errors import DuplicateKeyError

from app.models.tenant import DefaultRole, Tenant
from app.models.tenant_member import MemberRole, TenantMember
from app.models.user import User
from app.models.base import utcnow
from app.services.auth import hash_password
from app.repositories import UserRepository, TenantRepository


async def seed_admin_user() -> None:
    """Create a default admin user, tenant, and membership on first startup.

    Skips silently if any user already exists.
    """
    count = await User.find().count()
    if count > 0:
        return

    password = secrets.token_urlsafe(16)

    user = User(
        email="roberto.conterosito@applica.guru",
        display_name="Admin",
        password_hash=hash_password(password),
        email_verified=True,
    )
    try:
        await user.insert()
    except DuplicateKeyError:
        # Another instance beat us to it — skip silently
        return

    tenant = Tenant(
        name="Default",
        slug="default",
        default_role=DefaultRole.member,
    )
    try:
        await tenant.insert()
    except DuplicateKeyError:
        return

    membership = TenantMember(
        tenant_id=tenant.id,
        user_id=user.id,
        role=MemberRole.owner,
        joined_at=utcnow(),
    )
    try:
        await membership.insert()
    except DuplicateKeyError:
        pass

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
