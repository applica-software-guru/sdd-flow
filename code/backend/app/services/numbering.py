"""Numbering service: progressive numbers and unique slugs for CRs and bugs.

Shared by `BugService`, `ChangeRequestService` and `SyncService`; the caller
passes the repository that owns the target document type.
"""

import time
import uuid

from pymongo.errors import DuplicateKeyError

from app.models.bug import Bug
from app.models.change_request import ChangeRequest
from app.repositories import BugRepository, ChangeRequestRepository
from app.services.slug import parse_path_prefix, slugify


class NumberingService:
    def __init__(
        self,
        bug_repo: BugRepository,
        cr_repo: ChangeRequestRepository,
    ) -> None:
        self._bug_repo = bug_repo
        self._cr_repo = cr_repo

    async def assign_number_and_slug(
        self,
        doc: Bug | ChangeRequest,
        project_id: uuid.UUID,
        title: str,
        path: str | None = None,
        explicit_slug: str | None = None,
    ) -> tuple[int, str]:
        """Determine number and slug for a new CR or Bug and insert it.

        Priority:
        1. explicit_slug (UI-provided override), sanitised via slugify.
        2. slug parsed from a CLI `{number}-{slug}.md` path prefix.
        3. Otherwise, auto-increment number and slugify title.

        In both cases, ensure slug uniqueness within the project by appending
        -2, -3, etc. Catches DuplicateKeyError on concurrent insert collisions.
        """
        repo = self._repo_for(doc)
        path_number, path_slug = parse_path_prefix(path) if path else (None, None)

        # --- Determine number ---
        if path_number is not None:
            # Check if the number is already taken by a different entity
            existing = await repo.find_by_number(project_id, path_number)
            if existing is not None:
                # Fallback to auto-increment
                path_number = None

        if path_number is None:
            max_number = await repo.get_max_number(project_id)
            number = max_number + 1
        else:
            number = path_number

        # --- Determine slug ---
        if explicit_slug is not None:
            base_slug = slugify(explicit_slug)
        elif path_slug is not None:
            base_slug = path_slug
        else:
            base_slug = slugify(title)
        slug = base_slug
        suffix = 2

        for attempt in range(10):
            existing_slug = await repo.find_by_slug(project_id, slug)
            if existing_slug is None:
                doc.number = number
                doc.slug = slug
                try:
                    await doc.insert()
                    return number, slug
                except DuplicateKeyError:
                    # Slug or number collision from concurrent insert — increment suffix and retry
                    slug = f"{base_slug}-{suffix}"
                    suffix += 1
                    continue
            else:
                slug = f"{base_slug}-{suffix}"
                suffix += 1

        # Final fallback: try once more with timestamp-based uniqueness
        slug = f"{base_slug}-{int(time.time())}"
        doc.number = number
        doc.slug = slug
        await doc.insert()
        return number, slug

    def _repo_for(self, doc: Bug | ChangeRequest) -> BugRepository | ChangeRequestRepository:
        if isinstance(doc, Bug):
            return self._bug_repo
        return self._cr_repo
