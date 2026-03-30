import uuid
from datetime import datetime, timezone

from app.utils.bson import uuid_to_bin
from bson.binary import Binary, UuidRepresentation
from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth import ApiKeyContext, get_api_key_context, get_api_key_project
from app.models.bug import Bug, BugSeverity, BugStatus
from app.models.change_request import CRStatus, ChangeRequest
from app.models.document_file import DocStatus, DocumentFile
from app.models.project import Project
from app.models.base import utcnow
from app.repositories import BugRepository, ChangeRequestRepository, DocumentFileRepository
from app.schemas.bugs import BugBulkRequest, BugBulkResponse, BugDeleteRequest, BugDeleteResponse, BugEnrichRequest, BugResponse
from app.schemas.change_requests import CRBulkRequest, CRBulkResponse, CRDeleteRequest, CRDeleteResponse, CREnrichRequest, CRResponse
from app.schemas.docs import DocBulkRequest, DocBulkResponse, DocDeleteRequest, DocDeleteResponse, DocEnrichRequest, DocResponse
from app.schemas.projects import ProjectResetRequest, ProjectResetResponse
from app.services.project_reset import reset_project_data
from app.services.slug import assign_number_and_slug

router = APIRouter(prefix="/cli", tags=["cli"])




@router.get("/pending-crs", response_model=list[CRResponse])
async def pending_crs(
    project: Project = Depends(get_api_key_project),
):
    crs = await ChangeRequest.find(
        {
            "projectId": project.id,
            "status": {"$in": [CRStatus.draft.value, CRStatus.pending.value, CRStatus.approved.value]},
        }
    ).sort([("createdAt", -1)]).to_list()
    return crs


@router.get("/open-bugs", response_model=list[BugResponse])
async def open_bugs(
    project: Project = Depends(get_api_key_project),
):
    bugs = await Bug.find(
        {
            "projectId": project.id,
            "status": {"$in": [BugStatus.draft.value, BugStatus.open.value, BugStatus.in_progress.value]},
        }
    ).sort([("createdAt", -1)]).to_list()
    return bugs


@router.post("/crs/{cr_id}/applied", response_model=CRResponse)
async def mark_cr_applied(
    cr_id: uuid.UUID,
    project: Project = Depends(get_api_key_project),
):
    cr = await ChangeRequest.get(cr_id)
    if cr is None or cr.project_id != project.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")

    await cr.set({
        ChangeRequest.status: CRStatus.applied,
        ChangeRequest.closed_at: utcnow(),
    })
    cr = await ChangeRequest.get(cr_id)
    return cr


@router.post("/bugs/{bug_id}/resolved", response_model=BugResponse)
async def mark_bug_resolved(
    bug_id: uuid.UUID,
    project: Project = Depends(get_api_key_project),
):
    bug = await Bug.get(bug_id)
    if bug is None or bug.project_id != project.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    await bug.set({
        Bug.status: BugStatus.resolved,
        Bug.closed_at: utcnow(),
    })
    bug = await Bug.get(bug_id)
    return bug


@router.post("/push-docs", response_model=DocBulkResponse)
async def push_docs(
    body: DocBulkRequest,
    project: Project = Depends(get_api_key_project),
):
    doc_repo = DocumentFileRepository()
    created = 0
    updated = 0
    docs = []

    # Batch fetch existing docs by path
    paths = [item.path for item in body.documents]
    existing_map = await doc_repo.find_by_paths(project.id, paths)

    for item in body.documents:
        existing = existing_map.get(item.path)

        if existing is not None:
            await existing.set({
                DocumentFile.title: item.title,
                DocumentFile.content: item.content,
                DocumentFile.version: existing.version + 1,
                DocumentFile.status: item.status or DocStatus.synced,
            })
            refreshed = await doc_repo.find_by_id(existing.id)
            docs.append(refreshed)
            updated += 1
        else:
            doc = DocumentFile(
                project_id=project.id,
                path=item.path,
                title=item.title,
                content=item.content,
                status=item.status or DocStatus.synced,
                version=1,
            )
            await doc.insert()
            docs.append(doc)
            created += 1

    return DocBulkResponse(
        created=created,
        updated=updated,
        documents=[DocResponse.model_validate(d) for d in docs],
    )


@router.get("/pull-docs", response_model=list[DocResponse])
async def pull_docs(
    project: Project = Depends(get_api_key_project),
):
    docs = await DocumentFile.find(
        {
            "projectId": project.id,
            "status": {"$ne": DocStatus.deleted.value},
        }
    ).sort([("path", 1)]).to_list()
    return docs


@router.post("/docs/{doc_id}/enriched", response_model=DocResponse)
async def mark_doc_enriched(
    doc_id: uuid.UUID,
    body: DocEnrichRequest,
    project: Project = Depends(get_api_key_project),
):
    doc = await DocumentFile.get(doc_id)
    if doc is None or doc.project_id != project.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    await doc.set({
        DocumentFile.content: body.content,
        DocumentFile.status: DocStatus.new,
        DocumentFile.version: doc.version + 1,
    })
    doc = await DocumentFile.get(doc_id)
    return doc


@router.post("/crs/{cr_id}/enriched", response_model=CRResponse)
async def mark_cr_enriched(
    cr_id: uuid.UUID,
    body: CREnrichRequest,
    project: Project = Depends(get_api_key_project),
):
    cr = await ChangeRequest.get(cr_id)
    if cr is None or cr.project_id != project.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found")

    await cr.set({
        ChangeRequest.body: body.body,
        ChangeRequest.status: CRStatus.pending,
    })
    cr = await ChangeRequest.get(cr_id)
    return cr


@router.post("/bugs/{bug_id}/enriched", response_model=BugResponse)
async def mark_bug_enriched(
    bug_id: uuid.UUID,
    body: BugEnrichRequest,
    project: Project = Depends(get_api_key_project),
):
    bug = await Bug.get(bug_id)
    if bug is None or bug.project_id != project.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bug not found")

    await bug.set({
        Bug.body: body.body,
        Bug.status: BugStatus.open,
    })
    bug = await Bug.get(bug_id)
    return bug


@router.post("/push-crs", response_model=CRBulkResponse)
async def push_crs(
    body: CRBulkRequest,
    ctx: ApiKeyContext = Depends(get_api_key_context),
):
    cr_repo = ChangeRequestRepository()
    created = 0
    updated = 0
    crs = []

    # Batch fetch existing CRs by id
    ids_to_fetch = [item.id for item in body.change_requests if item.id is not None]
    existing_by_id: dict = {}
    if ids_to_fetch:
        id_bins = [uuid_to_bin(i) for i in ids_to_fetch]
        fetched = await ChangeRequest.find(
            {"_id": {"$in": id_bins}, "projectId": ctx.project.id}
        ).to_list()
        existing_by_id = {cr.id: cr for cr in fetched}

    for item in body.change_requests:
        existing = existing_by_id.get(item.id) if item.id else None

        if existing is not None:
            updates: dict = {}
            if item.path is not None:
                updates[ChangeRequest.path] = item.path
            if item.title is not None:
                updates[ChangeRequest.title] = item.title
            if item.body is not None:
                updates[ChangeRequest.body] = item.body
            if item.status is not None:
                updates[ChangeRequest.status] = item.status
            if updates:
                await existing.set(updates)
            refreshed = await cr_repo.find_by_id(existing.id)
            crs.append(refreshed)
            updated += 1
        else:
            cr = ChangeRequest(
                project_id=ctx.project.id,
                number=0,
                slug="",
                path=item.path,
                title=item.title,
                body=item.body,
                status=item.status or CRStatus.pending,
                author_id=ctx.user_id,
            )
            await assign_number_and_slug(
                cr, ctx.project.id, item.title, item.path, repo=cr_repo
            )
            crs.append(cr)
            created += 1

    return CRBulkResponse(
        created=created,
        updated=updated,
        change_requests=[CRResponse.model_validate(cr) for cr in crs],
    )


@router.post("/push-bugs", response_model=BugBulkResponse)
async def push_bugs(
    body: BugBulkRequest,
    ctx: ApiKeyContext = Depends(get_api_key_context),
):
    bug_repo = BugRepository()
    created = 0
    updated = 0
    bugs = []

    # Batch fetch existing bugs by id
    ids_to_fetch = [item.id for item in body.bugs if item.id is not None]
    existing_by_id: dict = {}
    if ids_to_fetch:
        id_bins = [uuid_to_bin(i) for i in ids_to_fetch]
        fetched = await Bug.find(
            {"_id": {"$in": id_bins}, "projectId": ctx.project.id}
        ).to_list()
        existing_by_id = {b.id: b for b in fetched}

    for item in body.bugs:
        existing = existing_by_id.get(item.id) if item.id else None

        if existing is not None:
            updates: dict = {}
            if item.path is not None:
                updates[Bug.path] = item.path
            if item.title is not None:
                updates[Bug.title] = item.title
            if item.body is not None:
                updates[Bug.body] = item.body
            if item.severity is not None:
                updates[Bug.severity] = item.severity
            if item.status is not None:
                updates[Bug.status] = item.status
            if updates:
                await existing.set(updates)
            refreshed = await bug_repo.find_by_id(existing.id)
            bugs.append(refreshed)
            updated += 1
        else:
            bug = Bug(
                project_id=ctx.project.id,
                number=0,
                slug="",
                path=item.path,
                title=item.title,
                body=item.body,
                status=item.status or BugStatus.draft,
                severity=item.severity,
                author_id=ctx.user_id,
            )
            await assign_number_and_slug(
                bug, ctx.project.id, item.title, item.path, repo=bug_repo
            )
            bugs.append(bug)
            created += 1

    return BugBulkResponse(
        created=created,
        updated=updated,
        bugs=[BugResponse.model_validate(bug) for bug in bugs],
    )


@router.post("/delete-docs", response_model=DocDeleteResponse)
async def delete_docs(
    body: DocDeleteRequest,
    project: Project = Depends(get_api_key_project),
):
    doc_repo = DocumentFileRepository()
    deleted = 0
    deleted_paths = []

    # Batch fetch existing docs by path
    existing_map = await doc_repo.find_by_paths(project.id, body.paths)

    for path in body.paths:
        doc = existing_map.get(path)
        if doc is not None and doc.status != DocStatus.deleted:
            await doc.set({DocumentFile.status: DocStatus.deleted})
            deleted += 1
            deleted_paths.append(path)

    return DocDeleteResponse(deleted=deleted, paths=deleted_paths)


@router.post("/delete-crs", response_model=CRDeleteResponse)
async def delete_crs(
    body: CRDeleteRequest,
    project: Project = Depends(get_api_key_project),
):
    deleted = 0
    deleted_paths = []

    for path in body.paths:
        cr = await ChangeRequest.find_one(
            {
                "projectId": project.id,
                "path": path,
                "status": {"$ne": CRStatus.deleted.value},
            }
        )
        if cr is not None:
            await cr.set({
                ChangeRequest.status: CRStatus.deleted,
                ChangeRequest.closed_at: utcnow(),
            })
            deleted += 1
            deleted_paths.append(path)

    return CRDeleteResponse(deleted=deleted, paths=deleted_paths)


@router.post("/delete-bugs", response_model=BugDeleteResponse)
async def delete_bugs(
    body: BugDeleteRequest,
    project: Project = Depends(get_api_key_project),
):
    deleted = 0
    deleted_paths = []

    for path in body.paths:
        bug = await Bug.find_one(
            {
                "projectId": project.id,
                "path": path,
                "status": {"$ne": BugStatus.deleted.value},
            }
        )
        if bug is not None:
            await bug.set({
                Bug.status: BugStatus.deleted,
                Bug.closed_at: utcnow(),
            })
            deleted += 1
            deleted_paths.append(path)

    return BugDeleteResponse(deleted=deleted, paths=deleted_paths)


@router.post("/reset", response_model=ProjectResetResponse)
async def cli_reset_project(
    body: ProjectResetRequest,
    ctx: ApiKeyContext = Depends(get_api_key_context),
):
    if body.confirm_slug != ctx.project.slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Slug mismatch: expected '{ctx.project.slug}'",
        )

    counts = await reset_project_data(ctx.project, ctx.project.tenant_id, ctx.user_id)
    return ProjectResetResponse(
        message=f"Project '{ctx.project.name}' has been reset",
        **counts,
    )
