---
title: "Backend service layer — class-based services with constructor injection and a DI composition root"
status: applied
author: "user"
created-at: "2026-09-04T00:00:00.000Z"
revision: "2"
---

# CR-036 (rev. 2): Backend Service Layer — Class-based Services + Dependency Injection

> **Revision 2** — supersedes the function-based service design of rev. 1.
> Rev. 1 introduced module-level service functions with optional repository
> parameters and inline default instantiation: rejected in review because it
> scatters singletons and does not provide real dependency injection.
> Rev. 2 mandates **service classes with constructor injection** and a single
> **composition root** (`app/dependencies.py`) that wires repositories into
> services and services into controllers, in the style already proven in the
> calzedonia-takt backend (`app/api/deps.py`).

## Summary

Refactor the backend so that:

1. **Controllers never touch repositories or Beanie models** — they receive
   fully-wired **service classes** via FastAPI dependency injection and only
   map input/output schemas.
2. **Domain services are classes** (`BugService`, `ProjectService`, …) whose
   repositories and collaborator services are injected through the
   constructor — no default instantiation, no module-level singletons
   scattered across modules.
3. **A single composition root** (`app/dependencies.py`) owns all wiring:
   repository providers and service factories. Tests substitute any component
   via `app.dependency_overrides[...]`.
4. The HTTP contract stays frozen; the entire existing test suite keeps
   passing (except white-box monkeypatches, which are migrated to the correct
   injection points).

Target layering:

```
controller (api/)  →  service class (services/)  →  repository (repositories/)  →  MongoDB
                              ▲
                              └── collaborators (AuditService, NotificationService, …)
        all wiring happens in dependencies.py (composition root)
```

## Current state (September 2026, after rev. 1 partial implementation)

- Rev. 1 moved all data access out of `app/api/` (zero repository imports and
  zero Beanie queries remain in controllers — verified) and introduced
  `app/dependencies.py` with repository providers.
- **Problem**: services were implemented as module-level functions with
  optional repository parameters defaulting to inline instantiation
  (`repo: BugRepository | None = None` → `repo = BugRepository()`).
  This is DI in name only: collaborators are hidden, wiring is implicit and
  duplicated at every call site, and tests cannot substitute components
  cleanly.
- The remaining work of rev. 1 (pyright clean-up in progress) is superseded by
  this revision: the service layer is redesigned before finishing the lint
  pass.

## Target design

### 1. Service classes with constructor injection

One class per domain in `app/services/`, repositories and collaborator
services injected through `__init__` and stored as private attributes:

```python
# app/services/bugs.py
class BugService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        bug_repo: BugRepository,
        comment_repo: CommentRepository,
        user_service: UserService,
        audit_service: AuditService,
        notification_service: NotificationService,
        assignment_service: AssignmentService,
        collaboration_service: CollaborationService,
    ) -> None:
        self._project_repo = project_repo
        self._bug_repo = bug_repo
        self._comment_repo = comment_repo
        self._user_service = user_service
        self._audit_service = audit_service
        self._notification_service = notification_service
        self._assignment_service = assignment_service
        self._collaboration_service = collaboration_service

    async def create_bug(self, tenant_id: UUID, project_id: UUID, body: BugCreate, actor_user_id: UUID) -> Bug: ...
    async def list_bugs(self, tenant_id: UUID, project_id: UUID, page: int, page_size: int, ...) -> tuple[list[Bug], int]: ...
    async def update_bug(self, tenant_id: UUID, project_id: UUID, bug_id: UUID, body: BugUpdate, actor_user_id: UUID) -> Bug: ...
    # assign / transition / comments / assignments history …
```

- Every parameter and return type is annotated (pyright-clean under the
  strict config).
- Services raise domain errors (`HTTPException` stays acceptable for
  not-found/conflict, as today) and return models/Beans; controllers map to
  response schemas.

### 2. Cross-cutting collaborators become services too

The stateful collaborators used by domain services are converted to classes:

| Class | Module | Replaces |
|---|---|---|
| `AuditService` | `services/audit.py` | `log_event`, `log_event_for_user_tenants`, `query_audit_log` |
| `NotificationService` | `services/notifications.py` | `create_notification` + notification/preference flows |
| `UserService` | `services/users.py` | `ensure_tenant_member`, `resolve_user_briefs` |
| `AssignmentService` | `services/assignment.py` | `apply_assignment`, `record_initial_assignment` |
| `CollaborationService` | `services/collab_notifications.py` | `notify_comment_added`, `notify_content_changed` |

Domain services receive these through the constructor; **no service calls
another service's module-level function**, and no service instantiates a
repository outside its constructor.

Pure utilities remain stateless function modules (no DI needed):
`slug.py` (`slugify`, `parse_path_prefix` — pure string logic), `email_templates.py`,
`mailer.py`, `agent_models.py`, `seed.py` (startup-only). The slug *numbering*
flow moves into the domain services that own the corresponding repository
(`BugService._assign_number_and_slug`, `ChangeRequestService._assign_number_and_slug`),
and prompt generation moves into `WorkerJobService`.

### 3. Single composition root: `app/dependencies.py`

Repositories are stateless; the composition root provides **per-request**
instances through FastAPI's dependency cache and builds services bottom-up:

```python
# app/dependencies.py — the ONLY place where concrete wiring happens

def get_project_repository() -> ProjectRepository:
    return ProjectRepository()

def get_bug_repository() -> BugRepository:
    return BugRepository()

# ... one provider per repository ...

def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(user_repo)

def get_audit_service(audit_repo: AuditRepository = Depends(get_audit_repository)) -> AuditService:
    return AuditService(audit_repo, user_service=Depends...  # composed from providers

def get_bug_service(
    project_repo: ProjectRepository = Depends(get_project_repository),
    bug_repo: BugRepository = Depends(get_bug_repository),
    comment_repo: CommentRepository = Depends(get_comment_repository),
    user_service: UserService = Depends(get_user_service),
    audit_service: AuditService = Depends(get_audit_service),
    notification_service: NotificationService = Depends(get_notification_service),
    assignment_service: AssignmentService = Depends(get_assignment_service),
    collaboration_service: CollaborationService = Depends(get_collaboration_service),
) -> BugService:
    return BugService(
        project_repo=project_repo,
        bug_repo=bug_repo,
        comment_repo=comment_repo,
        user_service=user_service,
        audit_service=audit_service,
        notification_service=notification_service,
        assignment_service=assignment_service,
        collaboration_service=collaboration_service,
    )
```

Rules:

- `dependencies.py` is the **only** module allowed to instantiate repositories
  and services. Services and repositories never construct their own
  collaborators.
- No module-level singleton service/repo instances: the composition root is
  the single source of wiring (stateless components make per-request
  construction cheap and test-friendly).

### 4. Controllers become thin

```python
@router.post("", response_model=BugResponse, status_code=status.HTTP_201_CREATED)
async def create_bug(
    tenant_id: uuid.UUID,
    project_id: uuid.UUID,
    body: BugCreate,
    member: TenantMember = Depends(get_current_tenant_member),
    svc: BugService = Depends(get_bug_service),
) -> BugResponse:
    bug = await svc.create_bug(tenant_id, project_id, body, member.user_id)
    return (await svc.enrich_bug_responses([BugResponse.model_validate(bug)], [bug]))[0]
```

- Controllers import **only** `app.dependencies` (providers), `app.middleware.auth`,
  schemas and models — never `app.repositories`, never Beanie models.
- Return types annotated on every handler.

### 5. Tests: component substitution the correct way

Existing integration tests stay black-box over HTTP (contract frozen, no test
changes needed). Any future test that must isolate logic overrides a provider:

```python
app.dependency_overrides[get_bug_service] = lambda: FakeBugService()
```

The one white-box monkeypatch that existed (`send_tenant_invitation_email`)
moves to the service layer it belongs to.

### 6. Toolchain (aligned with calzedonia-takt)

- `pyrightconfig.json` at `code/backend/` with `typeCheckingMode: standard` plus
  `reportUnknown*`/`reportMissingTypeArgument`/`reportUnnecessaryComparison` as
  errors, `include: ["app"]` — **0 errors** required.
- `pyproject.toml`: `[tool.ruff]` (`line-length = 100`, `select = ["E","F","I","UP","W"]`,
  isort `known-first-party = ["app"]`), `[tool.ruff.format]` double quotes.
- New `cli.sh` (same UX as calzedonia-takt): `install`, `start`, `test`, `lint`
  (ruff check + ruff format --check), `format`, `typecheck` (pyright), `check`,
  `shell`, `help`.
- Full typing of the services layer: no bare `dict`/`list` annotations, no
  untyped parameters, no inline repository default arguments.

## Implementation plan

### Phase A — Composition root and service classes

1. Convert the ten rev. 1 service modules to classes with constructor-injected
   repositories/collaborators: `BugService`, `ChangeRequestService`,
   `ProjectService`, `TenantService`, `DocumentService`, `ApiKeyService`,
   `NotificationService`, `WorkerJobService`, `SearchService`, `SyncService`.
2. Convert collaborators: `AuditService`, `UserService`, `AssignmentService`,
   `CollaborationService`; move slug numbering and prompt generation into the
   owning services (`BugService`/`ChangeRequestService`/`WorkerJobService`).
3. Rebuild `app/dependencies.py` as the single composition root (repo providers
   + service factories); delete every inline instantiation elsewhere.

### Phase B — Controllers

4. Rewrite controllers to inject service classes via `Depends(get_xxx_service)`;
   no repository imports, no Beanie queries, every handler return-annotated.
   Migration order: `projects` → `api_keys` → `notifications` → `docs` →
   `bugs` → `change_requests` → `tenants` → `auth` → `workers`/`workers_cli` →
   `search` → `cli` (one commit per domain, tests after each).

### Phase C — Toolchain and verification

5. Add `[tool.ruff]`/`[tool.ruff.format]` to `pyproject.toml`; run
   `ruff check --fix` + `ruff format`.
6. Strict pyrightconfig (calzedonia-takt rules) → drive `app/` to **0 errors**.
7. Add `cli.sh` (`lint`, `format`, `typecheck`, `check`, `test`, `start`).
8. Full test suite green (239 tests, unchanged except the single white-box
   monkeypatch migration already done in rev. 1).

### Phase D — Documentation sync

9. `system/architecture.md`: service-layer section rewritten for classes +
   composition root; backend tree updated (`dependencies.py`, service classes).
10. `sdd mark-synced` + commit per domain.

## Documentation changes to apply (when this revision is applied)

- `system/architecture.md`:
  - replace the "Service Layer" section with the class-based design:
    *"Domain services are classes with constructor-injected repositories and
    collaborator services; `app/dependencies.py` is the single composition
    root (repository providers + service factories); controllers receive
    services via `Depends(get_xxx_service)` and never import repositories"*
  - document the DI convention and the test substitution pattern
  - update the backend tree (`dependencies.py`, service classes)

## Out of scope

Unchanged from rev. 1: frontend, CLI contract, API schemas, MongoDB schema,
auth middleware redesign, third-party DI frameworks (we stay on FastAPI
`Depends` composition), rate limiting.

## Acceptance criteria

1. No `from app.repositories import ...` and no Beanie model queries inside `app/api/*.py`
2. No inline repository/service instantiation outside `app/dependencies.py`
   (`grep -rn "Repository()" app/api app/services` returns providers only)
3. Every domain service is a class with constructor injection; every handler
   has a fully annotated signature
4. All existing tests pass without behavioural changes (239 green)
5. `ruff check app/ tests/` and `ruff format --check app/ tests/` clean
6. `pyright` (strict config, `include: ["app"]`) reports **0 errors**
7. `system/architecture.md` updated and synced; `sdd validate` clean
8. `cli.sh lint|format|typecheck|check` available and passing