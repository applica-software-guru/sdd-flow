"""
Shared fixtures for the test suite.

Strategy:
- Each test gets its own AsyncSession that commits normally.
- Fixtures create data with unique slugs/emails so tests don't collide.
- Override ``get_current_user`` and ``get_current_tenant_member`` so that
  tests can call authenticated endpoints without real JWT tokens.
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.db.session import get_db
from app.main import app
from app.middleware.auth import get_current_user, get_current_tenant_member
from app.models.user import User
from app.models.tenant import Tenant, DefaultRole
from app.models.tenant_member import TenantMember, MemberRole
from app.models.project import Project


# ---------------------------------------------------------------------------
# Session-scoped event loop so all tests share the same loop and engine
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Engine / session factory (session-scoped, tied to the event loop above)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def _engine():
    eng = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
    yield eng
    # Can't do async cleanup in sync fixture — engine will be GC'd


@pytest_asyncio.fixture
async def db_session(_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


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
async def test_user(db_session: AsyncSession, unique_id: str) -> AsyncGenerator[User, None]:
    user = User(
        email=f"test-{unique_id}@example.com",
        display_name=f"Test User {unique_id}",
        password_hash="fakehash",
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    yield user
    # Cleanup
    try:
        await db_session.execute(delete(User).where(User.id == user.id))
        await db_session.commit()
    except Exception:
        await db_session.rollback()


# ---------------------------------------------------------------------------
# Tenant + membership
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_tenant(db_session: AsyncSession, test_user: User, unique_id: str) -> AsyncGenerator[Tenant, None]:
    tenant = Tenant(
        name=f"Test Tenant {unique_id}",
        slug=f"test-tenant-{unique_id}",
        default_role=DefaultRole.member,
    )
    db_session.add(tenant)
    await db_session.commit()

    member = TenantMember(
        tenant_id=tenant.id,
        user_id=test_user.id,
        role=MemberRole.owner,
    )
    db_session.add(member)
    await db_session.commit()
    yield tenant
    # Cleanup: members should cascade
    try:
        await db_session.execute(delete(Tenant).where(Tenant.id == tenant.id))
        await db_session.commit()
    except Exception:
        await db_session.rollback()


@pytest_asyncio.fixture
async def test_member(db_session: AsyncSession, test_tenant: Tenant, test_user: User) -> TenantMember:
    from sqlalchemy import select
    result = await db_session.execute(
        select(TenantMember).where(
            TenantMember.tenant_id == test_tenant.id,
            TenantMember.user_id == test_user.id,
        )
    )
    return result.scalar_one()


# ---------------------------------------------------------------------------
# Test project
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_project(db_session: AsyncSession, test_tenant: Tenant, unique_id: str) -> Project:
    project = Project(
        tenant_id=test_tenant.id,
        name=f"Test Project {unique_id}",
        slug=f"test-proj-{unique_id}",
        description="A test project",
    )
    db_session.add(project)
    await db_session.commit()
    return project


# ---------------------------------------------------------------------------
# Async HTTP client with dependency overrides
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
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
