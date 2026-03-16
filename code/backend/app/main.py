from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import auth, tenants, projects, change_requests, bugs, docs, api_keys, notifications, audit_log, search, cli
from app.db.session import async_session_factory
from app.services.seed import seed_admin_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_session_factory() as db:
        await seed_admin_user(db)
    yield


app = FastAPI(title="SDD Flow API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers under /api/v1
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


@app.get("/health")
async def health_check():
    return {"status": "ok"}
