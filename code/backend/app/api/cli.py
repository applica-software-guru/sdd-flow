import uuid

from fastapi import APIRouter, Depends

from app.dependencies import get_sync_service
from app.middleware.auth import ApiKeyContext, get_api_key_context, get_api_key_project
from app.models.project import Project
from app.schemas.bugs import (
    BugBulkRequest,
    BugBulkResponse,
    BugDeleteRequest,
    BugDeleteResponse,
    BugEnrichRequest,
    BugResponse,
)
from app.schemas.change_requests import (
    CRBulkRequest,
    CRBulkResponse,
    CRDeleteRequest,
    CRDeleteResponse,
    CREnrichRequest,
    CRResponse,
)
from app.schemas.docs import (
    DocBulkRequest,
    DocBulkResponse,
    DocDeleteRequest,
    DocDeleteResponse,
    DocEnrichRequest,
    DocResponse,
)
from app.schemas.projects import ProjectResetRequest, ProjectResetResponse
from app.services.sync import SyncService

router = APIRouter(prefix="/cli", tags=["cli"])


@router.get("/pending-crs", response_model=list[CRResponse])
async def pending_crs(
    project: Project = Depends(get_api_key_project),
    svc: SyncService = Depends(get_sync_service),
) -> list[CRResponse]:
    crs = await svc.pending_crs(project.id)
    return [CRResponse.model_validate(cr) for cr in crs]


@router.get("/open-bugs", response_model=list[BugResponse])
async def open_bugs(
    project: Project = Depends(get_api_key_project),
    svc: SyncService = Depends(get_sync_service),
) -> list[BugResponse]:
    bugs = await svc.open_bugs(project.id)
    return [BugResponse.model_validate(bug) for bug in bugs]


@router.get("/deleted-doc-ids", response_model=list[str])
async def deleted_doc_ids(
    project: Project = Depends(get_api_key_project),
    svc: SyncService = Depends(get_sync_service),
) -> list[str]:
    return [str(i) for i in await svc.deleted_doc_ids(project.id)]


@router.get("/deleted-cr-ids", response_model=list[str])
async def deleted_cr_ids(
    project: Project = Depends(get_api_key_project),
    svc: SyncService = Depends(get_sync_service),
) -> list[str]:
    return [str(i) for i in await svc.deleted_cr_ids(project.id)]


@router.get("/deleted-bug-ids", response_model=list[str])
async def deleted_bug_ids(
    project: Project = Depends(get_api_key_project),
    svc: SyncService = Depends(get_sync_service),
) -> list[str]:
    return [str(i) for i in await svc.deleted_bug_ids(project.id)]


@router.post("/crs/{cr_id}/applied", response_model=CRResponse)
async def mark_cr_applied(
    cr_id: uuid.UUID,
    project: Project = Depends(get_api_key_project),
    svc: SyncService = Depends(get_sync_service),
) -> CRResponse:
    return CRResponse.model_validate(await svc.mark_cr_applied(cr_id, project.id))


@router.post("/bugs/{bug_id}/resolved", response_model=BugResponse)
async def mark_bug_resolved(
    bug_id: uuid.UUID,
    project: Project = Depends(get_api_key_project),
    svc: SyncService = Depends(get_sync_service),
) -> BugResponse:
    return BugResponse.model_validate(await svc.mark_bug_resolved(bug_id, project.id))


@router.post("/push-docs", response_model=DocBulkResponse)
async def push_docs(
    body: DocBulkRequest,
    project: Project = Depends(get_api_key_project),
    svc: SyncService = Depends(get_sync_service),
) -> DocBulkResponse:
    created, updated, docs = await svc.push_docs(project.id, body.documents)
    return DocBulkResponse(
        created=created,
        updated=updated,
        documents=[DocResponse.model_validate(d) for d in docs],
    )


@router.get("/pull-docs", response_model=list[DocResponse])
async def pull_docs(
    project: Project = Depends(get_api_key_project),
    svc: SyncService = Depends(get_sync_service),
) -> list[DocResponse]:
    docs = await svc.pull_docs(project.id)
    return [DocResponse.model_validate(d) for d in docs]


@router.post("/docs/{doc_id}/enriched", response_model=DocResponse)
async def mark_doc_enriched(
    doc_id: uuid.UUID,
    body: DocEnrichRequest,
    project: Project = Depends(get_api_key_project),
    svc: SyncService = Depends(get_sync_service),
) -> DocResponse:
    return DocResponse.model_validate(await svc.mark_doc_enriched(doc_id, project.id, body.content))


@router.post("/crs/{cr_id}/enriched", response_model=CRResponse)
async def mark_cr_enriched(
    cr_id: uuid.UUID,
    body: CREnrichRequest,
    project: Project = Depends(get_api_key_project),
    svc: SyncService = Depends(get_sync_service),
) -> CRResponse:
    return CRResponse.model_validate(await svc.mark_cr_enriched(cr_id, project.id, body.body))


@router.post("/bugs/{bug_id}/enriched", response_model=BugResponse)
async def mark_bug_enriched(
    bug_id: uuid.UUID,
    body: BugEnrichRequest,
    project: Project = Depends(get_api_key_project),
    svc: SyncService = Depends(get_sync_service),
) -> BugResponse:
    return BugResponse.model_validate(await svc.mark_bug_enriched(bug_id, project.id, body.body))


@router.post("/push-crs", response_model=CRBulkResponse)
async def push_crs(
    body: CRBulkRequest,
    ctx: ApiKeyContext = Depends(get_api_key_context),
    svc: SyncService = Depends(get_sync_service),
) -> CRBulkResponse:
    created, updated, crs = await svc.push_crs(ctx.project.id, ctx.user_id, body.change_requests)
    return CRBulkResponse(
        created=created,
        updated=updated,
        change_requests=[CRResponse.model_validate(cr) for cr in crs],
    )


@router.post("/push-bugs", response_model=BugBulkResponse)
async def push_bugs(
    body: BugBulkRequest,
    ctx: ApiKeyContext = Depends(get_api_key_context),
    svc: SyncService = Depends(get_sync_service),
) -> BugBulkResponse:
    created, updated, bugs = await svc.push_bugs(ctx.project.id, ctx.user_id, body.bugs)
    return BugBulkResponse(
        created=created,
        updated=updated,
        bugs=[BugResponse.model_validate(bug) for bug in bugs],
    )


@router.post("/delete-docs", response_model=DocDeleteResponse)
async def delete_docs(
    body: DocDeleteRequest,
    project: Project = Depends(get_api_key_project),
    svc: SyncService = Depends(get_sync_service),
) -> DocDeleteResponse:
    deleted, deleted_paths = await svc.delete_docs(project.id, body.paths)
    return DocDeleteResponse(deleted=deleted, paths=deleted_paths)


@router.post("/delete-crs", response_model=CRDeleteResponse)
async def delete_crs(
    body: CRDeleteRequest,
    project: Project = Depends(get_api_key_project),
    svc: SyncService = Depends(get_sync_service),
) -> CRDeleteResponse:
    deleted, deleted_paths = await svc.delete_crs(project.id, body.paths)
    return CRDeleteResponse(deleted=deleted, paths=deleted_paths)


@router.post("/delete-bugs", response_model=BugDeleteResponse)
async def delete_bugs(
    body: BugDeleteRequest,
    project: Project = Depends(get_api_key_project),
    svc: SyncService = Depends(get_sync_service),
) -> BugDeleteResponse:
    deleted, deleted_paths = await svc.delete_bugs(project.id, body.paths)
    return BugDeleteResponse(deleted=deleted, paths=deleted_paths)


@router.post("/reset", response_model=ProjectResetResponse)
async def cli_reset_project(
    body: ProjectResetRequest,
    ctx: ApiKeyContext = Depends(get_api_key_context),
    svc: SyncService = Depends(get_sync_service),
) -> ProjectResetResponse:
    counts = await svc.reset_project(ctx.project, body.confirm_slug, ctx.user_id)
    return ProjectResetResponse(
        message=f"Project '{ctx.project.name}' has been reset",
        **counts,
    )
