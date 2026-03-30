---
title: "MongoDB Migration and Backend Refactoring"
status: applied
author: "roberto"
created-at: "2026-03-28T00:00:00.000Z"
---

# MongoDB Migration and Backend Refactoring

## Summary

Replace the PostgreSQL relational database with MongoDB, introduce a clean Repository pattern, refactor the service layer, and address a set of security vulnerabilities and bugs discovered during the analysis. All SQL-related infrastructure (SQLAlchemy, Alembic, asyncpg, PostgreSQL) is removed; no data migration is required.

---

## Motivation

The current backend relies on a synchronous-style ORM (SQLAlchemy async) over PostgreSQL. The domain model is document-oriented by nature (CRs, bugs, docs, audit entries with arbitrary JSON payloads), making MongoDB a natural fit. Moving to MongoDB also allows us to:

- Eliminate Alembic migrations entirely — schema evolution is handled by the application layer
- Adopt a proper Repository pattern, decoupling data access from business logic
- Simplify infrastructure (one less service in Docker Compose and CI)
- Fix several security and correctness issues identified during the analysis

---

## Analysis Notes

Before reading this CR, the following files were analyzed in full:
`app/api/workers.py`, `app/api/workers_cli.py`, `app/api/change_requests.py`, `app/api/auth.py`, `app/api/search.py`, `app/services/auth.py`, `app/services/slug.py`, `app/services/seed.py`, `app/services/project_reset.py`, `app/middleware/auth.py`, `app/main.py`, `app/models/*`, `tests/conftest.py`, `tests/test_auth.py`, `tests/test_bugs.py`, `tests/test_change_requests.py`, `tests/test_cli.py`, `tests/test_search.py`, `tests/test_tenants.py`, `tests/test_projects.py`, `pyproject.toml`, `.github/workflows/ci.yml`.

---

## Technology Decision: Beanie 2.x + PyMongo Async

> **Important**: Motor (the previous standard async MongoDB driver) was officially deprecated by MongoDB Inc. on May 14, 2025, with EOL on May 14, 2026. New projects must not start on Motor.

The chosen stack is:

- **`pymongo >= 4.10`** (with built-in async API via `AsyncMongoClient`) — the official MongoDB async driver, replacing Motor. Uses native Python asyncio instead of thread delegation; benchmarks show improved latency and throughput.
- **`beanie >= 2.1`** — the standard async ODM for FastAPI+MongoDB. As of Beanie 2.0 (July 2025), it dropped Motor and migrated to the `pymongo` async API internally. Beanie 2.1 (March 2026) requires Python ≥ 3.10 and MongoDB ≥ 7.0, both already met by this project.

Beanie is chosen over raw PyMongo because:
- Document models are Pydantic v2 `BaseModel` subclasses — zero impedance mismatch with FastAPI request/response models
- Declarative index definitions on the model class (replaces Alembic migration files)
- Built-in query DSL, pagination helpers, and aggregation support
- 2.3M PyPI downloads/month, 4,400+ dependent projects, team-based governance, endorsed by MongoDB Developer blog

**Known Beanie 2.x caveats to handle at implementation time**:

| Caveat | Mitigation |
|---|---|
| `datetime` loses timezone info on round-trip | Pass `tz_aware=True` to `AsyncMongoClient(mongodb_url, tz_aware=True)` |
| `revision_id` feature has a stale `_previous_revision_id` bug (#707) | Do not use `revision_id` on any document model |
| `AliasGenerator` not fully respected in serialization (#1033) | Use explicit `Field(alias="camelCaseName")` on every multi-word field; avoid `AliasGenerator` entirely |
| Atomic operations require dropping to `get_pymongo_collection()` | Documented per-case below |
| No automatic `updated_at` on save (unlike SQLAlchemy `onupdate`) | Implement via Beanie `@before_event` hook — see Section 3 |

---

## Critical Architecture Difference: No Foreign Key Cascades

**This is the single most important structural difference from PostgreSQL.** SQLAlchemy models use `ondelete="CASCADE"` extensively:

- `ChangeRequest`, `Bug`, `DocumentFile`, `ApiKey`, `Worker` all cascade from `Project`
- `WorkerJobMessage` cascades from `WorkerJob`
- `TenantMember`, `TenantInvitation` cascade from `Tenant`
- `Comment` references `ChangeRequest` or `Bug` by `entity_id`

**In MongoDB, none of these cascades exist.** Every delete operation in the application layer must explicitly handle all dependent documents. A missed cascade leaves orphan documents that are invisible to users but accumulate in the database.

**Rule**: Any service method that deletes an entity is responsible for deleting all documents that reference it. This must be verified and enforced during implementation. See Section 5 (Cascade Delete Map) for the complete reference.

---

## Scope

### 1. Remove all SQL infrastructure

- Delete `alembic/` directory and all migration files
- Delete `alembic.ini`
- Delete `app/db/session.py` and `app/db/base.py`
- Delete `app/models/` directory entirely (all SQLAlchemy model files)
- Remove from `pyproject.toml`: `sqlalchemy`, `alembic`, `asyncpg`, `psycopg2-binary`

### 2. Add MongoDB async stack

Add to `pyproject.toml`:
- `pymongo[srv] >= 4.10` — official async MongoDB driver (includes `AsyncMongoClient`; `[srv]` extra required for Atlas `mongodb+srv://` connection strings)
- `beanie >= 2.1` — async ODM built on PyMongo async + Pydantic v2
- `slowapi >= 0.1.9` — rate limiting for FastAPI (see SEC-002)

Update `.env.example`:
```
MONGODB_URL=mongodb://localhost:27017/sddflow
```

Remove `DATABASE_URL`.

### 3. Rewrite data models as Beanie Documents

#### Base document classes

Two base classes are defined in `app/models/base.py`. Which one a model inherits from depends on whether the entity is mutable.

**`BaseDocument`** — for mutable entities (user-facing records that get updated):
```python
from beanie import Document, before_event, Replace, Update
from pydantic import Field
from uuid import UUID, uuid4
from datetime import datetime, timezone

class BaseDocument(Document):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @before_event(Replace, Update)
    def _set_updated_at(self):
        self.updated_at = datetime.now(timezone.utc)
```

The `@before_event` hook fires automatically on every `save()`, `replace()`, or `update()`. This replaces SQLAlchemy's `onupdate=func.now()`. **Without this, `updated_at` would never be refreshed throughout the entire codebase.**

**`ImmutableDocument`** — for append-only entities that must NOT have `updated_at`:
```python
class ImmutableDocument(Document):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

This is used for `AuditLogEntry` (immutable by design — adding `updated_at` would be semantically wrong), `WorkerJobMessage` (append-only log lines), and `Notification` (has `read_at` but no general `updated_at`).

#### Handling of existing non-standard fields

Several current SQLAlchemy models do NOT inherit `TimestampMixin` and have no `updated_at`:
- `ApiKey` — only `created_at`
- `TenantMember` — only `joined_at` (no `created_at`, no `updated_at`)
- `Notification` — only `created_at` and `read_at`
- `WorkerJobMessage` — only `created_at`
- `AuditLogEntry` — only `created_at`

In the Beanie models:
- `ApiKey` inherits `BaseDocument` — gains `updated_at` (harmless, set on revocation update)
- `TenantMember` inherits `BaseDocument` — retains `joined_at` as a semantic field distinct from `created_at`; both coexist
- `Worker` — current model has `registered_at` (via `server_default`) plus `created_at`/`updated_at` from `TimestampMixin`. In Beanie, `Worker(BaseDocument)` provides `created_at` and `updated_at`. Rename `registered_at` → alias to `created_at`, OR keep `registered_at` as a dedicated field set on first insert. Keeping it as a separate field is cleaner for the API response schema (`WorkerResponse` exposes `registered_at`)
- `Notification` inherits `ImmutableDocument` — retains `read_at` field; no `updated_at`
- `AuditLogEntry`, `WorkerJobMessage` inherit `ImmutableDocument`

#### Model files

- `app/models/base.py` — `BaseDocument`, `ImmutableDocument` (new)
- `app/models/user.py` — `User(BaseDocument)`
- `app/models/tenant.py` — `Tenant(BaseDocument)`, `TenantMember(BaseDocument)`, `TenantInvitation(BaseDocument)`
- `app/models/project.py` — `Project(BaseDocument)`, `ApiKey(BaseDocument)`
- `app/models/document_file.py` — `DocumentFile(BaseDocument)`
- `app/models/change_request.py` — `ChangeRequest(BaseDocument)`
- `app/models/bug.py` — `Bug(BaseDocument)`
- `app/models/comment.py` — `Comment(BaseDocument)` — **single file, single collection** with `entity_type: Literal["change_request", "bug"]` and `entity_id: UUID` discriminator (same structure as the current SQL table; do not split into separate CR/Bug comment classes)
- `app/models/audit.py` — `AuditLogEntry(ImmutableDocument)`
- `app/models/notification.py` — `Notification(ImmutableDocument)`, `NotificationPreference(BaseDocument)`
- `app/models/auth.py` — `RefreshToken(BaseDocument)`, `PasswordResetToken(BaseDocument)`
- `app/models/worker.py` — `Worker(BaseDocument)`, `WorkerJob(BaseDocument)`, `WorkerJobMessage(ImmutableDocument)`

**Relationship accessor elimination**: The current SQLAlchemy models declare 16 `relationship()` fields across the codebase (e.g., `project.workers`, `bug.comments`, `worker_job.messages`). Beanie has no lazy-loading — accessing any of these attributes on a Beanie Document will either return `None` silently or raise `AttributeError` at runtime. Every call site that traverses a relationship must be replaced with an explicit query. During implementation, grep for `\.comments`, `\.workers`, `\.jobs`, `\.messages`, `\.members`, `\.invitations`, `\.api_keys` on model instances to locate all such accesses.

**ID strategy**: keep `id: UUID` as the Beanie document `id` field (stored as string in MongoDB `_id`). This preserves all existing API response shapes and frontend TypeScript types without change.

All `datetime` fields must carry timezone info — the `tz_aware=True` client option ensures they round-trip correctly from MongoDB.

**Indexes declared on each model class** (replaces all Alembic unique constraints and indexes):

| Collection | Index |
|---|---|
| User | `email` (unique) |
| User | `google_id` (sparse unique) |
| Tenant | `slug` (unique) |
| TenantMember | `(tenant_id, user_id)` (unique compound) |
| TenantInvitation | `token` (unique) |
| Project | `(tenant_id, slug)` (unique compound) |
| ApiKey | `key_hash` (unique) |
| DocumentFile | `(project_id, path)` (unique compound) |
| ChangeRequest | `(project_id, number)` (unique), `(project_id, slug)` (unique) |
| Bug | `(project_id, number)` (unique), `(project_id, slug)` (unique) |
| Comment | `entity_id`, `(entity_type, entity_id)` |
| AuditLogEntry | `(tenant_id, created_at)`, `(tenant_id, event_type)` |
| Notification | `(user_id, read_at)` |
| NotificationPreference | `(user_id, event_type)` (unique compound) |
| TenantInvitation | `expires_at` (TTL — auto-expire invitations) |
| Worker | `(project_id, name)` (unique) |
| WorkerJob | `(project_id, status)` |
| WorkerJobMessage | `(job_id, sequence)` |
| RefreshToken | `token_hash` (unique), `expires_at` (TTL — auto-expire) |
| PasswordResetToken | `token_hash` (unique), `expires_at` (TTL — auto-expire) |

`RefreshToken` and `PasswordResetToken` use MongoDB TTL indexes — documents are automatically deleted when `expires_at` is reached. No manual cleanup code needed.

### 4. Introduce Repository layer

Create `app/repositories/` with one repository per aggregate root:

```
app/repositories/
├── __init__.py
├── base.py                    # BaseRepository[T] with typed find_by_id, save, delete
├── user_repository.py
├── tenant_repository.py
├── project_repository.py
├── document_file_repository.py
├── change_request_repository.py
├── bug_repository.py
├── comment_repository.py
├── audit_repository.py
├── notification_repository.py
├── auth_repository.py         # RefreshToken, PasswordResetToken
└── worker_repository.py       # Worker, WorkerJob, WorkerJobMessage
```

Each repository:
- Accepts and returns typed Beanie document instances (no raw dicts)
- Owns all query construction for its collection
- Exposes a `find_page(filter, page, page_size) -> tuple[list[T], int]` helper returning items + total count
- Does **not** contain business logic — that stays in services

Repositories are stateless classes. FastAPI `Depends()` injection:

```python
def get_user_repository() -> UserRepository:
    return UserRepository()
```

Since there is no database session object to pass (Beanie operates at the class level globally), repositories are instantiated with no arguments.

### 5. Cascade Delete Map

This table defines what each service must explicitly delete when removing an entity. These are not automatic — every entry is a required code path.

| Deleted entity | Must also delete |
|---|---|
| `Project` | `DocumentFile`, `ChangeRequest`, `Bug`, `Comment` (for CRs and Bugs), `Notification` (for CRs, Bugs, Docs), `ApiKey`, `Worker`, `WorkerJob` (and their `WorkerJobMessage`), `AuditLogEntry` *scoped to project* |
| `ChangeRequest` | `Comment` where `entity_type=change_request, entity_id=cr.id` |
| `Bug` | `Comment` where `entity_type=bug, entity_id=bug.id` |
| `WorkerJob` | `WorkerJobMessage` where `job_id=job.id` |
| `Tenant` | all `TenantMember`, `TenantInvitation`, all `Project` records (triggering Project cascade above) |
| `User` | `RefreshToken`, `PasswordResetToken`, `TenantMember` (all tenants), `Notification` |

**Current `project_reset.py` gap**: The existing service already handles the reset correctly for SQL (FK cascades from Project handle ApiKey, Worker, WorkerJob, WorkerJobMessage automatically). In MongoDB this cascade is lost. `project_reset.py` must be extended to explicitly:
1. Cancel running WorkerJobs (BUG-003)
2. Delete all WorkerJobMessages for those jobs
3. Delete all WorkerJobs for the project
4. Delete all Workers for the project
5. Delete all ApiKeys for the project
6. Then delete Comments, Notifications, Bugs, CRs, DocumentFiles (already present)

### 6. Refactor services to use repositories

All services in `app/services/` are updated to call repositories instead of issuing ORM queries directly:

- `auth.py` — uses `UserRepository`, `AuthRepository`
- `audit.py` — uses `AuditRepository`
- `notifications.py` — uses `NotificationRepository`
- `password_reset.py` — uses `AuthRepository` (atomic token deletion)
- `slug.py` — uses `ChangeRequestRepository` / `BugRepository` for number/slug assignment
- `project_reset.py` — uses all relevant repositories per the Cascade Delete Map above
- `seed.py` — uses `UserRepository`, `TenantRepository`; catches `DuplicateKeyError` silently (see ARCH-001)
- `worker_prompt.py` — **NOT pure** — takes `db: AsyncSession`, queries `ChangeRequest`, `Bug`, `DocumentFile`, and calls `_fetch_comments()` which issues one `User` lookup per comment (N+1). Must be fully rewritten to use `ChangeRequestRepository`, `BugRepository`, `DocumentFileRepository`, and batch-load comment authors in 2 round-trips (see BUG-008)

### 7. Rewrite `middleware/auth.py`

The current auth middleware uses `Depends(get_db)` in four functions: `get_current_user`, `get_current_tenant_member`, `get_api_key_context`, `get_api_key_project`. With Beanie there is no `get_db` session to inject.

All four functions must be rewritten to use Beanie document queries directly:

```python
# Before (SQLAlchemy)
async def get_current_user(db: AsyncSession = Depends(get_db), ...):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

# After (Beanie)
async def get_current_user(...):
    user = await User.get(user_id)
```

The `get_api_key_context` and `get_api_key_project` functions update `last_used_at` after authenticating. Replace the SQL `UPDATE` with Beanie:

```python
await api_key.set({ApiKey.last_used_at: datetime.now(timezone.utc)})
```

This is the `partial update` API in Beanie — it only updates the specified fields without loading and re-saving the entire document.

### 8. Replace full-text search

The current global search uses PostgreSQL `ILIKE '%query%'` — a **substring** match, case-insensitive. This is a critical behavioral detail.

**MongoDB `$text` search is NOT a drop-in replacement**: it is word-based (stemmed full-text search). Searching for `"log"` would NOT match `"login"` with `$text`. This would be a silent behavioral regression.

**Correct replacement**: use `$regex` with case-insensitive flag:

```python
import re
pattern = re.compile(re.escape(query), re.IGNORECASE)
results = await ChangeRequest.find(
    {"$or": [{"title": pattern}, {"body": pattern}]},
    ChangeRequest.project_id.in_(project_ids),
).to_list()
```

**Performance note**: `$regex` with a non-anchored pattern (no `^`) cannot use a B-tree index and performs a collection scan. This matches the current behavior (PostgreSQL `ILIKE '%q%'` also does a full scan without a trigram index). At current scale this is acceptable. If the collections grow large, the upgrade path is to Atlas Search (Lucene-based), which is a configuration change, not a code change.

Each collection is queried independently and results are merged before returning. The `tenant_id` scope is enforced by filtering on project IDs that belong to the tenant. The search endpoint response shape is unchanged.

**AuditLogEntry search**: the current SQL implementation searches `event_type.ilike(pattern)` AND `cast(details, String).ilike(pattern)` (a JSONB-to-string cast). In MongoDB, the `details` field is a native document — searching inside nested fields via regex requires `$where` (slow, insecure). **Replace with regex on `event_type` only**, dropping the `details` deep-search:

```python
audit_results = await AuditLogEntry.find(
    AuditLogEntry.tenant_id == tenant_id,
    {"event_type": pattern},
).to_list()
```

This preserves the `audit_log` type in the search response (keeping the existing `test_search_returns_all_entity_types` and `test_search_filter_by_type_audit_log` tests passing — those tests use `event_type="cr.created.foobar"` and search for `"foobar"`, which matches via regex on `event_type`). No test changes needed for search.

### 9. Rewrite `workers_cli.py` poll and cleanup logic

`workers_cli.py` contains three patterns that interact directly with the database and must all change together:

#### 9a. Remove `_cleanup_stale_workers` from `workers_cli.py`

The current code calls `_cleanup_stale_workers(db, project_id)` in two places:
- `heartbeat()` handler — every heartbeat (potentially every few seconds)
- `poll_job()` handler — every 1-second iteration inside the 30-second long-poll loop

With the proactive background task (Section 10), these calls become both redundant and harmful (they run complex multi-document updates on every heartbeat and poll iteration). **Remove `_cleanup_stale_workers` entirely from `workers_cli.py`** — the background task is the only place stale detection runs.

#### 9b. Rewrite `poll_job` long-poll loop

The current `poll_job` uses:
```python
for _ in range(POLL_DURATION):
    job = await db.execute(select(WorkerJob)...with_for_update(skip_locked=True))
    if job:
        job.status = "assigned"
        await db.flush()
        return job
    await db.commit()       # ← releases and re-acquires SQLAlchemy transaction
    await asyncio.sleep(1)
```

The `await db.commit()` inside the loop is required with SQLAlchemy to see new rows committed by other requests. With Beanie, every query reads current data without transaction management — `await db.commit()` disappears.

Replace the entire `SELECT ... FOR UPDATE SKIP LOCKED` + flush pattern with the atomic MongoDB operation:

```python
for _ in range(POLL_DURATION):
    col = WorkerJob.get_pymongo_collection()
    raw = await col.find_one_and_update(
        {"project_id": str(project.id), "status": "queued"},
        {"$set": {"status": "assigned", "worker_id": str(worker_id),
                  "updated_at": utcnow()}},
        sort=[("created_at", 1)],
        return_document=True,
    )
    if raw:
        job = await WorkerJob.get(raw["_id"])
        await worker.set({Worker.status: WorkerStatus.busy,
                          Worker.last_heartbeat_at: utcnow()})
        return WorkerJobAssignment(...)
    await asyncio.sleep(1)
return Response(status_code=204)
```

#### 9c. Worker registration upsert

The current `register_worker` reads the worker, then creates or updates:
```python
worker = result.scalar_one_or_none()
if worker is not None:
    worker.status = WorkerStatus.online
    ...
else:
    worker = Worker(...)
    db.add(worker)
```

With MongoDB, replace with an atomic upsert via `find_one_and_update(..., upsert=True)`:

```python
col = Worker.get_pymongo_collection()
raw = await col.find_one_and_update(
    {"project_id": str(project.id), "name": body.name},
    {"$set": {"status": "online", "agent": body.agent, "branch": body.branch,
              "last_heartbeat_at": utcnow(), "metadata_": body.metadata},
     "$setOnInsert": {"id": str(uuid4()), "created_at": utcnow(),
                      "registered_at": utcnow()}},
    upsert=True,
    return_document=True,
)
worker = await Worker.get(raw["_id"])
```

This prevents a `DuplicateKeyError` race on concurrent register calls with the same worker name.

### 10. Background stale-worker monitor

Register an asyncio background task in the FastAPI lifespan that runs every 30 seconds:

```python
async def _monitor_stale_workers():
    while True:
        await asyncio.sleep(30)
        await worker_repository.mark_stale_workers_offline()
        await worker_repository.fail_orphaned_jobs()
```

The coroutine is started with `asyncio.create_task()` in the lifespan `startup` phase and cancelled in the `shutdown` phase. Thresholds remain unchanged (60 s → offline, 5 min + running job → failed).

**Multi-instance behavior**: each Cloud Run instance runs its own monitor. Both may attempt to mark the same stale worker offline simultaneously. This is safe: MongoDB document-level atomicity means one `updateOne` wins and the other is a no-op (the status is already `offline`).

### 11. Update database initialization

Replace `app/db/session.py` with `app/db/mongodb.py`:

```python
from beanie import init_beanie
from pymongo import AsyncMongoClient   # pymongo 4.10+ built-in async

async def init_db(mongodb_url: str):
    client = AsyncMongoClient(mongodb_url, tz_aware=True)
    db = client.get_default_database()
    await init_beanie(database=db, document_models=[...all Document classes...])
    return client
```

Store the `client` instance on `app.state` and call `client.close()` during lifespan shutdown. Call `init_db()` in the FastAPI lifespan hook (already exists in `main.py`).

### 12. Update config

In `app/config.py`:
- Replace `DATABASE_URL: str` with `MONGODB_URL: str`
- Add a Pydantic `@field_validator("JWT_SECRET")` that raises `ValueError` if the value is shorter than 32 characters or equals known weak defaults (SEC-004)

### 13. Update Docker Compose

In `docker-compose.yml`:
- Remove the `postgres` service and its named volume
- Add:

```yaml
mongo:
  image: mongo:7
  environment:
    MONGO_INITDB_DATABASE: sddflow
  volumes:
    - mongo_data:/data/db
  ports:
    - "27017:27017"
```

- Update backend environment: `MONGODB_URL=mongodb://mongo:27017/sddflow`
- Remove all `DATABASE_URL` references

### 14. Update CI pipeline

In `.github/workflows/ci.yml`:
- Replace the PostgreSQL service container with MongoDB, **including a health check** (without it, the test step may start before MongoDB accepts connections):

```yaml
services:
  mongodb:
    image: mongo:7
    ports:
      - 27017:27017
    options: >-
      --health-cmd "mongosh --eval 'db.adminCommand(\"ping\")'"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

- Set env var: `MONGODB_URL=mongodb://localhost:27017/sddtest`
- Remove `DATABASE_URL` from the test environment
- **Remove the `Run migrations` step** (`uv run alembic upgrade head`) entirely — Beanie creates indexes automatically on `init_beanie()`. There are no migrations with MongoDB.

### 15. Rewrite tests (full migration strategy)

The existing test suite uses SQLAlchemy patterns (`AsyncSession`, `db_session.add()`, `select()`, `delete()`). These must be completely replaced with Beanie/MongoDB equivalents. All existing test cases and assertions are preserved — only the infrastructure beneath them changes.

#### New `conftest.py` strategy

```python
# Session-scoped: initialize Beanie once per test run
# pyproject.toml already has asyncio_default_fixture_loop_scope = "session" — no extra config needed
@pytest_asyncio.fixture(scope="session")
async def init_mongodb():
    client = AsyncMongoClient("mongodb://localhost:27017/sddtest", tz_aware=True)
    await init_beanie(database=client.get_default_database(), document_models=[...])
    yield
    client.close()

# Function-scoped: clear all documents before each test (IMPORTANT: use delete_many, NOT drop)
@pytest_asyncio.fixture(autouse=True)
async def clean_db(init_mongodb):
    for model in [User, Tenant, TenantMember, TenantInvitation, Project, ApiKey,
                  DocumentFile, ChangeRequest, Bug, Comment, AuditLogEntry,
                  Notification, NotificationPreference, RefreshToken,
                  PasswordResetToken, Worker, WorkerJob, WorkerJobMessage]:
        await model.get_pymongo_collection().delete_many({})
```

**Critical**: use `delete_many({})`, NOT `drop()`. `drop()` destroys the collection including its indexes. Since `init_beanie()` runs only once (session scope), indexes are created only once. If `drop()` is used between tests, indexes are gone for all subsequent tests, and unique constraint violations will not be detected — tests that expect `409 Conflict` will silently start returning `201`.

#### Fixture translation table

| Old (SQLAlchemy) | New (Beanie) |
|---|---|
| `db_session.add(obj)` + `commit()` | `await obj.insert()` |
| `db_session.flush()` | (not needed — inserts are immediately visible) |
| `db_session.refresh(obj)` | `await obj.sync()` |
| `select(Model).where(...)` | `await Model.find_one(Model.field == value)` |
| `delete(Model).where(...)` | `await Model.find(Model.id == id).delete()` |
| `db_session.execute(select(...))` | `await Model.find(...).to_list()` |
| `result.scalar_one_or_none()` | `await Model.find_one(...)` (returns `None` if absent) |

#### Dependency override changes

`override_get_db` is removed entirely (no `get_db` dependency in the new code — middleware uses Beanie directly). The `auth_client` fixture in `test_auth.py` that currently only overrides `get_db` becomes a plain httpx client with ASGITransport — no overrides needed, because the app naturally uses the test database (since `init_db` was called with the test URL).

Auth overrides for the main `client` fixture remain unchanged:

```python
app.dependency_overrides[get_current_user] = lambda: test_user
app.dependency_overrides[get_current_tenant_member] = lambda tenant_id=None: test_member
```

#### Test-specific SQL patterns to migrate

- **Creating `ApiKey`**: `await ApiKey(...).insert()`
- **Creating `PasswordResetToken`**: `await PasswordResetToken(...).insert()`
- **Creating `RefreshToken`**: `await RefreshToken(...).insert()`
- **Checking token deletion after reset** (`test_reset_password_success`): the test currently checks `updated_token.used_at is not None`. With SEC-003, the token is deleted (not marked) — change assertion to `await PasswordResetToken.find_one(PasswordResetToken.id == token_id) is None`
- **Verifying refresh token revocation**: `assert await RefreshToken.find(RefreshToken.user_id == user.id).count() == 0`

#### Duplicate key error handling

Tests that verify unique constraint violations (e.g. `test_register_duplicate_email`) expect `409 Conflict`. Route handlers must catch `DuplicateKeyError` from pymongo (replacing `IntegrityError` from SQLAlchemy):

```python
from pymongo.errors import DuplicateKeyError
```

Test assertions (`assert resp.status_code == 409`) are unchanged. **This only works if indexes are preserved between tests** — which is why `delete_many` (not `drop`) is mandatory in `clean_db`.

---

## Architecture Notes

### ARCH-001 — Seed service race condition on multi-instance startup

**Problem**: `seed.py` checks `User.count() == 0` before creating the admin user. If two Cloud Run instances start simultaneously, both may see 0 users and both attempt to insert the admin user and the default tenant.

**Fix**: The `email` unique index on `User` and the `slug` unique index on `Tenant` will cause one of the concurrent inserts to fail with `DuplicateKeyError`. The seed function must catch this and skip silently:

```python
try:
    await user.insert()
except DuplicateKeyError:
    return  # Another instance seeded first
```

### ARCH-002 — `slowapi` IP extraction behind Cloud Run

**Problem**: Cloud Run runs behind Google's load balancer. `request.client.host` always returns the load balancer's internal IP, not the client IP. All users would share a single rate-limit bucket, breaking the per-IP limiting entirely.

**Fix**: Configure `slowapi` to extract the real client IP from the `X-Forwarded-For` header:

```python
from slowapi import Limiter
from fastapi import Request

def _get_real_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host or "unknown"

limiter = Limiter(key_func=_get_real_ip)
```

### ARCH-003 — SSE stream must not close over a SQLAlchemy session

The `stream_worker_job` endpoint in `workers.py` uses a nested `event_generator()` coroutine that captures `db: AsyncSession` from the outer scope:

```python
async def event_generator():
    while True:
        msg_result = await db.execute(...)     # outer db session held open
        await db.refresh(job)                  # outer db session held open
        await asyncio.sleep(0.5)
```

This holds a SQLAlchemy connection from the pool open for the entire duration of the SSE stream (potentially minutes per active job). This is a **pre-existing connection starvation risk** that is resolved by the MongoDB migration.

With Beanie, there is no session to close over. The generator performs direct Beanie queries — each query independently acquires and releases a connection from the pool:

```python
async def event_generator():
    last_sequence = 0
    while True:
        messages = await WorkerJobMessage.find(
            WorkerJobMessage.job_id == job_id,
            WorkerJobMessage.sequence > last_sequence,
        ).sort("+sequence").to_list()
        for msg in messages:
            yield f"data: {json.dumps(...)}\n\n"
            last_sequence = msg.sequence
        current_job = await WorkerJob.get(job_id)
        if current_job.status in (JobStatus.completed, JobStatus.failed, JobStatus.cancelled):
            yield f"event: done\ndata: ...\n\n"
            break
        await asyncio.sleep(0.5)
```

The generator is self-contained — no closure over external state. This pattern is correct and must be used in the implementation.

### ARCH-004 — Rate limiter bypass in tests

`slowapi` rate limiting must be **disabled in the test environment** to prevent test interference (multiple tests calling the same endpoint within a minute would hit the rate limit and produce unexpected `429` responses).

Add a `TESTING: bool = False` flag to `app/config.py`. In `app/api/auth.py`, wrap the `@limiter.limit(...)` decorators:

```python
if not settings.TESTING:
    @limiter.limit("10/minute")
    async def login(...):
        ...
```

Or more cleanly, configure `slowapi` with a custom backend that's a no-op when `settings.TESTING` is true:

```python
limiter = Limiter(
    key_func=_get_real_ip,
    enabled=not settings.TESTING,
)
```

In `pyproject.toml`, the test runner should set `TESTING=true` via the `[tool.pytest.ini_options]` `env` option or via `conftest.py` at session start.

### ARCH-005 — MongoDB single-node has no multi-document transactions

**Problem**: Docker Compose and CI use `mongo:7` as a **single-node** replica (not a replica set). Multi-document ACID transactions in MongoDB require a replica set. Without it, `async with await session.start_transaction()` raises `InvalidOperation` at runtime.

**Affected operations** that currently rely on implicit SQL transaction atomicity:

| Operation | Documents involved | Risk without transaction |
|---|---|---|
| `POST /auth/register` | `User` insert + `RefreshToken` insert | User created but no token issued; retry gets 409 |
| `POST /auth/google` | same | same |
| `POST /tenant/...` | `Tenant` + `TenantMember` inserts | Tenant with no owner |
| `DELETE /projects/{id}` | cascade across 8+ collections | partial deletion |

**Mitigation strategy** (no replica set required):

1. **Insert the most critical document first** (e.g., `User` before `RefreshToken`) and treat the second insert as best-effort. If `RefreshToken` insert fails, the user can re-login to get a token — no data corruption.
2. **Cascade deletes are idempotent** — partial deletes can be retried safely since each `delete_many` is a no-op if already deleted.
3. **For Cloud Run production (Atlas)**: Atlas always runs as a replica set. Enable transactions by initializing the client with a session where needed. The Docker Compose `mongo:7` can be converted to a single-node replica set by adding `--replSet rs0` to the command and calling `rs.initiate()` in an init script if transaction guarantees are required during local development.

**Action**: Document this caveat in `system/architecture.md`. Do NOT use multi-document transactions in the initial implementation. Design all write sequences so that partial completion is safe to retry.

### ARCH-006 — `metadata_` field alias in `Worker` model

**Problem**: Python reserves `metadata` as a SQLAlchemy column attribute name collision risk; the current model uses `metadata_` as the field name. In MongoDB, the stored field name should be clean (`metadata`, not `metadata_`).

**Fix**: In `Worker(BaseDocument)`, declare:

```python
metadata_: dict = Field(default_factory=dict, alias="metadata")
```

With `model_config = ConfigDict(populate_by_name=True)`, Python code can use `worker.metadata_` while MongoDB stores the field as `metadata`. The `WorkerResponse` schema serializes as `"metadata"` in the JSON response (already the expected key). This is already used in the Section 9c `find_one_and_update` snippet — ensure the model declaration matches.

---

## Security Fixes

### SEC-001 — Refresh tokens not invalidated on password change

**Problem**: When a user resets their password, existing refresh tokens remain valid. An attacker who captured a refresh token before the reset can still obtain new access tokens.

**Fix**: `AuthRepository` implements `revoke_all_refresh_tokens(user_id: UUID)` which deletes all `RefreshToken` documents for the user. Called by `password_reset.py` immediately after a successful password update. Test `test_reset_password_success` must assert zero remaining refresh tokens.

### SEC-002 — No rate limiting on authentication endpoints

**Problem**: `POST /auth/login`, `POST /auth/register`, and `POST /auth/forgot-password` have no rate limiting — vulnerable to brute-force and email enumeration.

**Fix**: Add `slowapi` as a dependency. Apply per-IP limits (with real IP extraction — see ARCH-002):
- `POST /auth/login`: 10 req/minute
- `POST /auth/forgot-password`: 5 req/minute
- `POST /auth/register`: 5 req/minute

Return `429 Too Many Requests` with `Retry-After` header. Rate limiter must be disabled or mocked in tests to avoid test interference.

### SEC-003 — Password reset token not invalidated atomically

**Problem**: `PasswordResetToken` is deleted *after* the password update. A concurrent second request with the same token races through validity check before deletion.

**Fix**: Atomic find-and-delete:

```python
col = PasswordResetToken.get_pymongo_collection()
token_doc = await col.find_one_and_delete(
    {"token_hash": hashed, "expires_at": {"$gt": utcnow()}}
)
if not token_doc:
    raise HTTPException(400, "Invalid or expired reset token")
await update_password(user_id, new_password)
```

Token is deleted as the first operation. The `used_at` field is removed from the model (no longer needed — document is deleted, not marked).

### SEC-004 — JWT_SECRET accepts weak values silently

**Problem**: If deployed with a short or known-default secret, JWT tokens are trivially forgeable.

**Fix**:

```python
@field_validator("JWT_SECRET")
@classmethod
def jwt_secret_must_be_strong(cls, v: str) -> str:
    weak = {"change-me-in-production", "secret", "changeme", ""}
    if len(v) < 32 or v in weak:
        raise ValueError("JWT_SECRET must be at least 32 characters and not a known weak value")
    return v
```

The application refuses to start with a weak secret.

### SEC-005 — Terminal status transitions not guarded

**Problem**: The ChangeRequest and Bug status machines allow transitions out of `deleted` and `closed` states.

**Fix**: In both transition endpoints:

```python
if entity.status in ("deleted", "closed"):
    raise HTTPException(409, f"Cannot transition a {entity.status} item")
```

Document `deleted` as a valid terminal status in `entities.md` for both entities.

---

## Bug Fixes

### BUG-001 — Worker stale detection only runs on demand

**Problem**: Stale detection is on-the-fly during GET requests. A stuck job goes undetected until someone queries the worker list.

**Fix**: Proactive 30-second background task (see Section 10). GET endpoint becomes a pure read.

### BUG-002 — N+1 queries in tenant member listing

**Problem**: `GET /tenants/{tenant_id}/members` issues one `User` lookup per member.

**Fix**: `TenantRepository.find_members_with_users()` resolves all users in 2 round-trips:

```python
members = await TenantMember.find(TenantMember.tenant_id == tenant_id).to_list()
user_ids = [m.user_id for m in members]
users = await User.find({"_id": {"$in": [str(uid) for uid in user_ids]}}).to_list()
users_by_id = {u.id: u for u in users}
```

### BUG-003 — `project_reset` does not cancel running worker jobs

**Problem**: Active `WorkerJob` records are left running after a project reset.

**Fix**: `project_reset.py` cancels all non-terminal jobs first (see Section 5 Cascade Delete Map for the full deletion order).

### BUG-004 — N+1 queries in `list_worker_jobs`

**Problem**: `GET /worker-jobs` iterates over each job in the page and issues two separate DB queries per job:
1. `select(Worker.name).where(Worker.id == job.worker_id)` — one per job with a worker
2. `_get_entity_title(db, job.entity_type, job.entity_id)` — one per job with an entity

For a page of 20 jobs this can be up to 40 queries. This is a more severe N+1 than BUG-002 because jobs are frequently listed and each can have both a worker and an entity.

**Fix**: Batch all lookups before building the response:

```python
jobs = await WorkerJob.find(...).to_list()

# Batch worker name resolution
worker_ids = {j.worker_id for j in jobs if j.worker_id}
workers = await Worker.find({"_id": {"$in": [str(wid) for wid in worker_ids]}}).to_list()
workers_by_id = {w.id: w.name for w in workers}

# Batch entity title resolution (one query per entity type present in the page)
cr_ids = [j.entity_id for j in jobs if j.entity_type == "change_request" and j.entity_id]
bug_ids = [j.entity_id for j in jobs if j.entity_type == "bug" and j.entity_id]
doc_ids = [j.entity_id for j in jobs if j.entity_type == "document" and j.entity_id]
# fetch all at once...
```

Maximum 4 round-trips regardless of page size (workers + 3 entity types).

### BUG-005 — `request_password_reset` non-atomic delete + insert

**Problem**: `password_reset.py:request_password_reset()` first deletes any existing `PasswordResetToken` for the user, then inserts a new one. Between the delete and the insert, a concurrent second request sees no token and inserts its own — both get inserted, and the first caller receives a token that gets deleted by the race. This is a low-probability race but has security implications (stale tokens accepted).

**Fix**: Replace delete + insert with a single `find_one_and_replace` (upsert):

```python
col = PasswordResetToken.get_pymongo_collection()
new_doc = PasswordResetToken(user_id=user.id, token_hash=hashed, expires_at=expires)
await col.find_one_and_replace(
    {"user_id": str(user.id)},
    new_doc.model_dump(by_alias=True),
    upsert=True,
)
```

One atomic operation: if a token for this user exists, it is replaced; otherwise a new one is created. No window for a race.

### BUG-006 — Slug uniqueness check is not atomic

**Problem**: `assign_number_and_slug()` in `services/slug.py` reads the max slug counter then inserts. Two concurrent requests can both pass the read check with the same slug and then one gets a `DuplicateKeyError` at insert — currently this propagates as a 500.

**Fix**: Remove the pre-check loop entirely. Attempt insert directly, catch `DuplicateKeyError`, increment suffix, retry:

```python
for suffix in range(1, 11):
    candidate = base_slug if suffix == 1 else f"{base_slug}-{suffix}"
    try:
        doc.slug = candidate
        await doc.insert()
        return doc
    except DuplicateKeyError:
        continue
raise RuntimeError("Could not assign a unique slug after 10 attempts")
```

The unique compound index on `(project_id, slug)` is the enforcement mechanism. The existing `while True` loop with a SELECT pre-check in `slug.py` is replaced entirely by this pattern.

### BUG-007 — N+1 queries in project stats (`list_projects`)

**Problem**: `_project_response()` in `projects.py` issues 3 separate `COUNT` queries per project:
1. `select(func.count()).where(DocumentFile.project_id == project.id)` — doc count
2. `select(func.count()).where(ChangeRequest.project_id == ..., status=="open")` — open CRs
3. `select(func.count()).where(Bug.project_id == ..., status=="open")` — open bugs

Called once per project in `list_projects` → for 20 projects this is 60 COUNT queries in a single request.

**Fix**: Batch with `$group` aggregation pipelines — one query per collection returning counts for all project IDs at once:

```python
project_ids = [str(p.id) for p in projects]

doc_pipeline = [
    {"$match": {"project_id": {"$in": project_ids}}},
    {"$group": {"_id": "$project_id", "count": {"$sum": 1}}}
]
doc_counts = {r["_id"]: r["count"] for r in
              await DocumentFile.get_pymongo_collection().aggregate(doc_pipeline).to_list(None)}
# Same pattern for open CRs and open Bugs
```

Maximum 3 round-trips regardless of page size (one per entity collection).

### BUG-008 — N+1 queries in `worker_prompt.py` comment author lookup

**Problem**: `worker_prompt.py:_fetch_comments()` queries the `User` table once per comment to get the author's name:

```python
for comment in comments:
    author = await db.execute(select(User).where(User.id == comment.user_id))
    # author is fetched individually per comment
```

For a CR or Bug with 10 comments this issues 10 separate `User` queries.

**Fix**: Batch load all authors in 2 round-trips:

```python
comments = await Comment.find(
    Comment.entity_type == entity_type,
    Comment.entity_id == entity_id,
).sort("+created_at").to_list()

user_ids = list({c.user_id for c in comments})
users = await User.find({"_id": {"$in": [str(uid) for uid in user_ids]}}).to_list()
users_by_id = {u.id: u for u in users}
```

### BUG-009 — N+1 queries in CLI bulk push operations (`cli.py`)

**Problem**: `push_docs`, `push_crs`, and `push_bugs` in `cli.py` query the database once per item in the payload:

```python
for item in body.items:
    existing = await db.execute(select(DocumentFile).where(path=item.path))  # N queries
    if existing:
        existing.content = item.content
        ...
    else:
        await assign_number_and_slug(db, ...)
```

A `push_docs` call with 50 documents issues 50 individual `find_one` queries.

**Fix**: Batch fetch before the loop:

```python
paths = [item.path for item in body.items]
existing_docs = await DocumentFile.find(
    DocumentFile.project_id == project_id,
    {"path": {"$in": paths}},
).to_list()
existing_by_path = {d.path: d for d in existing_docs}

for item in body.items:
    if item.path in existing_by_path:
        await existing_by_path[item.path].set({"content": item.content, ...})
    else:
        await assign_number_and_slug(...)
```

Reduces to 1 fetch query + N upsert writes. Apply the same pattern to `push_crs` and `push_bugs`.

---

## Additional Optimizations

### OPT-001 — Connection pool tuning for Cloud Run

```python
AsyncMongoClient(
    mongodb_url,
    tz_aware=True,
    maxPoolSize=50,
    minPoolSize=5,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=3000,
)
```

### OPT-002 — Cursor-based pagination for `WorkerJobMessage`

Jobs can accumulate thousands of messages. Replace offset/limit with cursor-based pagination using the `sequence` field:

```
GET /worker-jobs/{id}?after_sequence=50&limit=100
```

O(log n) with the `(job_id, sequence)` index. Return last sequence in response for the client to continue.

### OPT-003 — Cloud Run MONGODB_URL injection

Inject `MONGODB_URL` as a Cloud Run environment variable. For Atlas or any `mongodb+srv://` URL, the `pymongo[srv]` extra (included in dependencies) handles DNS SRV resolution automatically. No code change needed — only Cloud Run service configuration.

---

## Files to Create / Modify

### New files
- `app/models/base.py` — `BaseDocument` (mutable) + `ImmutableDocument` (append-only, no `updated_at`)
- `app/models/comment.py` — single `Comment(BaseDocument)` for all entity types
- `app/db/mongodb.py` — PyMongo async client init + Beanie bootstrap
- `app/repositories/__init__.py`
- `app/repositories/base.py`
- `app/repositories/user_repository.py`
- `app/repositories/tenant_repository.py`
- `app/repositories/project_repository.py`
- `app/repositories/document_file_repository.py`
- `app/repositories/change_request_repository.py`
- `app/repositories/bug_repository.py`
- `app/repositories/comment_repository.py`
- `app/repositories/audit_repository.py`
- `app/repositories/notification_repository.py`
- `app/repositories/auth_repository.py`
- `app/repositories/worker_repository.py`

### Fully rewritten files
- `app/models/*.py` — all model files (Beanie Documents)
- `app/middleware/auth.py` — remove all `Depends(get_db)`, use Beanie queries directly; fix IP extraction for rate limiting
- `app/config.py` — `MONGODB_URL`, JWT_SECRET validator, remove `DATABASE_URL`
- `app/main.py` — lifespan: `init_db()`, stale worker task, MongoClient lifecycle
- `app/services/auth.py` — use repositories, add `revoke_all_refresh_tokens`
- `app/services/audit.py` — use `AuditRepository`
- `app/services/notifications.py` — use `NotificationRepository`
- `app/services/password_reset.py` — atomic token deletion (SEC-003), revoke refresh tokens (SEC-001)
- `app/services/slug.py` — retry-on-DuplicateKeyError (BUG-005)
- `app/services/project_reset.py` — full cascade deletion per map in Section 5 (BUG-003); update `ProjectResetResponse` to include counts for workers, jobs, messages deleted
- `app/services/seed.py` — Beanie queries, catch `DuplicateKeyError` silently (ARCH-001)
- `app/services/worker_prompt.py` — full rewrite: replace `db: AsyncSession` with direct repository queries; fix comment author N+1 (BUG-008)
- `app/api/*.py` — all route handlers: inject repositories via `Depends()`, catch `DuplicateKeyError`
- `app/api/workers.py` — rewrite SSE `event_generator()` without session closure (ARCH-003); fix N+1 in `list_worker_jobs` (BUG-004)
- `app/api/workers_cli.py` — remove `_cleanup_stale_workers`; rewrite `poll_job` with `find_one_and_update`; upsert worker registration (Section 9)
- `app/api/cli.py` — batch fetch before loop in `push_docs`/`push_crs`/`push_bugs` (BUG-009)
- `app/api/projects.py` — replace `_project_response` 3×COUNT per project with aggregation batch (BUG-007)
- `app/api/search.py` — replace `ILIKE` with `$regex`; replace JSONB `details` search with `event_type` regex only
- `tests/conftest.py` — Beanie fixture, `autouse` + `delete_many` (not `drop`) per test
- `tests/test_auth.py` — remove `db_session`, use `await Model.insert()` / `find_one()`; update `used_at` assertion
- `tests/test_bugs.py`, `test_change_requests.py`, `test_docs.py`, `test_projects.py`, `test_tenants.py`, `test_search.py` — remove `db_session` dependency
- `tests/test_cli.py` — replace `db_session.add(ApiKey(...))` with `await ApiKey(...).insert()`
- `tests/test_health.py` — update health check endpoint test if it probes DB connectivity (PostgreSQL → MongoDB)
- `tests/test_api_keys.py` — replace `db_session` fixtures with Beanie inserts
- `pyproject.toml` — add `pymongo[srv]>=4.10`, `beanie>=2.1`, `slowapi>=0.1.9`; remove SQL deps
- `docker-compose.yml` — replace `postgres` with `mongo:7`
- `.env.example` — replace `DATABASE_URL` with `MONGODB_URL`
- `.github/workflows/ci.yml` — replace postgres service container with MongoDB 7

### Deleted files
- `alembic/` (entire directory)
- `alembic.ini`
- `app/db/session.py`
- `app/db/base.py`

### Infrastructure files to update
- `Dockerfile` — remove `COPY alembic/ alembic/` and `COPY alembic.ini .` lines (Alembic is gone; leaving them in causes a build failure if the directories don't exist)

---

## Field Naming Convention (MongoDB Storage)

MongoDB has no enforced naming convention, but the community standard is **camelCase** for field names (e.g., `tenantId` instead of `tenant_id`). This CR must decide the storage convention upfront, because changing it after implementation requires a data migration.

**Chosen approach: camelCase in MongoDB, snake_case in Python.**

Beanie + Pydantic v2 supports this via `Field(alias="camelCase")` with `model_config = ConfigDict(populate_by_name=True)`:

```python
class TenantMember(BaseDocument):
    model_config = ConfigDict(populate_by_name=True)

    tenant_id: UUID = Field(alias="tenantId")
    user_id: UUID = Field(alias="userId")
    joined_at: datetime = Field(alias="joinedAt")
```

- Python code uses `member.tenant_id` (snake_case)
- MongoDB stores `{"tenantId": "..."}` (camelCase)
- API JSON responses: **keep snake_case** (pass `by_alias=False` in Pydantic serialization), preserving all existing TypeScript frontend types unchanged

**Implementation rules**:

1. Every `Field` with a multi-word name must declare an explicit `alias` (camelCase). Do NOT use `AliasGenerator` — it has a known Beanie 2.x bug (#1033) affecting serialization.
2. All models must include `model_config = ConfigDict(populate_by_name=True)` so Beanie can find documents by their Python attribute name in queries.
3. Beanie query syntax uses Python attribute names (`TenantMember.tenant_id == id` not `TenantMember.tenantId`) — this works transparently with `populate_by_name=True`.
4. Single-word field names (`id`, `email`, `slug`, `body`, `status`, `agent`, `branch`, `token`) require no alias.
5. Special case: `metadata_` uses `Field(alias="metadata")` for both the Python-reserved-name reason AND camelCase alignment.
6. `created_at` / `updated_at` / `read_at` / `expires_at` / `last_used_at` → aliases: `createdAt`, `updatedAt`, `readAt`, `expiresAt`, `lastUsedAt`

**Scope**: add the alias declarations to every model during the model rewrite in Section 3. This is low-overhead to do now and expensive to retrofit later.

### Documentation files to update
- `system/tech-stack.md` — replace SQLAlchemy/Alembic/PostgreSQL with PyMongo/Beanie/MongoDB 7; remove Alembic from Development tools
- `system/architecture.md` — update backend section, monorepo structure (add `repositories/`, rename `models/`), Database section (MongoDB, $regex search, TTL indexes, camelCase storage with snake_case Python/API convention), CI section, Repository Pattern section, remove tsvector/JSONB
- `system/entities.md` — replace FK language with "reference to", note indexes declared in model classes, document `deleted` as terminal status for ChangeRequest and Bug, remove `used_at` from PasswordResetToken
