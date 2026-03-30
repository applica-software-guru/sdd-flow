"""
Shared fixtures for the test suite.

Strategy:
- Each test gets a fresh MongoDB connection via Beanie.
- Fixtures create data with unique slugs/emails so tests don't collide.
- Override ``get_current_user`` and ``get_current_tenant_member`` so that
  tests can call authenticated endpoints without real JWT tokens.
"""

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app
from app.middleware.auth import get_current_user, get_current_tenant_member
from app.models.user import User
from app.models.tenant import Tenant, DefaultRole
from app.models.tenant_member import TenantMember, MemberRole
from app.models.project import Project
from app.db.mongodb import init_db


# ---------------------------------------------------------------------------
# MongoDB init (session-scoped)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session", autouse=True)
async def _mongodb():
    client = await init_db(settings.MONGODB_URL)
    yield
    await client.close()


# ---------------------------------------------------------------------------
# Unique IDs per test
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
def unique_id() -> str:
    return uuid.uuid4().hex[:8]


# ---------------------------------------------------------------------------
# Test user
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_user(unique_id: str) -> AsyncGenerator[User, None]:
    user = User(
        email=f"test-{unique_id}@example.com",
        display_name=f"Test User {unique_id}",
        password_hash="fakehash",
        email_verified=True,
    )
    await user.insert()
    yield user
    # Cleanup
    try:
        await user.delete()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Tenant + membership
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_tenant(test_user: User, unique_id: str) -> AsyncGenerator[Tenant, None]:
    tenant = Tenant(
        name=f"Test Tenant {unique_id}",
        slug=f"test-tenant-{unique_id}",
        default_role=DefaultRole.member,
    )
    await tenant.insert()

    member = TenantMember(
        tenant_id=tenant.id,
        user_id=test_user.id,
        role=MemberRole.owner,
    )
    await member.insert()

    yield tenant

    # Cleanup
    try:
        await TenantMember.find({"tenantId": tenant.id}).delete()
        await tenant.delete()
    except Exception:
        pass


@pytest_asyncio.fixture
async def test_member(test_tenant: Tenant, test_user: User) -> TenantMember:
    member = await TenantMember.find_one(
        {"tenantId": test_tenant.id, "userId": test_user.id}
    )
    return member


# ---------------------------------------------------------------------------
# Test project
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_project(test_tenant: Tenant, unique_id: str) -> Project:
    project = Project(
        tenant_id=test_tenant.id,
        name=f"Test Project {unique_id}",
        slug=f"test-proj-{unique_id}",
        description="A test project",
    )
    await project.insert()
    return project


# ---------------------------------------------------------------------------
# Async HTTP client with dependency overrides
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client(
    test_user: User,
    test_tenant: Tenant,
    test_member: TenantMember,
) -> AsyncGenerator[AsyncClient, None]:

    async def override_get_current_user():
        return test_user

    async def override_get_current_tenant_member(
        tenant_id: uuid.UUID = None,
    ):
        return test_member

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_tenant_member] = override_get_current_tenant_member

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
