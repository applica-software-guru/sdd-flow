import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.api import auth, tenants, projects, change_requests, bugs, docs, api_keys, notifications, audit_log, search, cli, workers, workers_cli
from app.db.mongodb import init_db


async def _monitor_stale_workers():
    from app.repositories.worker_repository import WorkerRepository
    repo = WorkerRepository()
    while True:
        await asyncio.sleep(30)
        try:
            await repo.mark_stale_workers_offline()
            await repo.fail_orphaned_jobs()
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = await init_db(settings.MONGODB_URL)
    app.state.mongodb_client = client
    from app.services.seed import seed_admin_user
    await seed_admin_user()
    monitor_task = asyncio.create_task(_monitor_stale_workers())
    yield
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass
    await client.close()


app = FastAPI(title="SDD Flow API", version="0.1.0", lifespan=lifespan)

# Register slowapi rate limiter
app.state.limiter = auth.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(tenants.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(change_requests.router, prefix="/api/v1")
app.include_router(bugs.router, prefix="/api/v1")
app.include_router(docs.router, prefix="/api/v1")
app.include_router(api_keys.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(audit_log.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(cli.router, prefix="/api/v1")
app.include_router(workers_cli.router, prefix="/api/v1")
app.include_router(workers.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
