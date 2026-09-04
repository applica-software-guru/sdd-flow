---
title: "Allow custom slug when creating CRs and bugs"
status: pending
author: "user"
created-at: "2026-07-16T00:00:00.000Z"
---

## Summary

When creating a CR or a bug from the UI, the slug (and therefore the filename) is always auto-derived from the title via `slugify(title)`. There is no way to override it. Users need control over the slug at creation time so that the resulting filename (e.g. `001-my-chosen-name.md`) is meaningful and stable without having to rename it later.

---

## Analysis

### Current implementation

**Backend — slug derivation (`services/slug.py`)**

`assign_number_and_slug` determines slug priority as follows:

1. If `path` contains a `{number}-{slug}.md` prefix (CLI flow), extract slug from the path.
2. Otherwise, call `slugify(title)`.

When invoked from the REST create endpoints (`POST /change-requests`, `POST /bugs`), `path` is `None`, so the slug is always derived from the title:

```python
# api/change_requests.py — line 51
await assign_number_and_slug(cr, project_id, body.title, repo=cr_repo)
#                                              ^^^^^^^^^^  no path → slug = slugify(title)
```

**Backend — `CRCreate` schema (`schemas/change_requests.py`)**

```python
class CRCreate(BaseModel):
    title: str
    body: str
    assignee_id: uuid.UUID | None = None
    target_files: list[str] | None = None
    # no slug field
```

The same applies to `BugCreate` in `schemas/bugs.py`.

**Frontend — `CreatePage.tsx` (CRs and bugs)**

The form sends only `title`, `body`, and `assignee_id`. No slug field is present.

---

## Required changes

### 1. `schemas/change_requests.py`

Add an optional `slug` field to `CRCreate`:

```python
class CRCreate(BaseModel):
    title: str
    body: str
    slug: str | None = None          # ← new
    assignee_id: uuid.UUID | None = None
    target_files: list[str] | None = None
```

### 2. `schemas/bugs.py`

Add an optional `slug` field to `BugCreate`:

```python
class BugCreate(BaseModel):
    title: str
    body: str
    slug: str | None = None          # ← new
    severity: BugSeverity | None = None
    assignee_id: uuid.UUID | None = None
```

### 3. `services/slug.py` — `assign_number_and_slug`

Add an `explicit_slug: str | None = None` parameter. When provided, use it as `base_slug` with the highest priority (above both `path_slug` and `slugify(title)`):

```python
async def assign_number_and_slug(
    doc,
    project_id: uuid.UUID,
    title: str,
    path: str | None = None,
    explicit_slug: str | None = None,   # ← new
    repo: ChangeRequestRepository | BugRepository = None,
) -> tuple[int, str]:
    path_number, path_slug = parse_path_prefix(path) if path else (None, None)

    # ... number logic unchanged ...

    # --- Determine slug ---
    if explicit_slug is not None:
        base_slug = slugify(explicit_slug)   # sanitise user input
    elif path_slug is not None:
        base_slug = path_slug
    else:
        base_slug = slugify(title)
    # ... uniqueness loop unchanged ...
```

Note: `explicit_slug` is passed through `slugify()` to ensure it contains only safe characters, even if the user typed something unexpected.

### 4. `api/change_requests.py` — `create_cr`

Pass `body.slug` as `explicit_slug`:

```python
await assign_number_and_slug(
    cr, project_id, body.title,
    explicit_slug=body.slug,
    repo=cr_repo,
)
```

### 5. `api/bugs.py` — `create_bug`

Same pattern as above for bugs.

### 6. Frontend — `CreatePage.tsx` for CRs (`pages/change-requests/CreatePage.tsx`)

Add a slug field between the title and description. The field:

- Auto-derives its value from the title using a `slugify` helper (matching backend logic) while the user has not manually edited it.
- Once the user edits the slug field directly, auto-fill stops (controlled mode).
- Shows a read-only hint: `Filename: change-requests/NNN-{slug}.md` where `NNN` is a placeholder.
- Sends the slug value to `createCR.mutateAsync`.

```tsx
function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'untitled';
}

export default function CreatePage() {
  const [title, setTitle]           = useState('');
  const [slug, setSlug]             = useState('');
  const [slugEdited, setSlugEdited] = useState(false);

  const handleTitleChange = (value: string) => {
    setTitle(value);
    if (!slugEdited) setSlug(slugify(value));
  };

  const handleSlugChange = (value: string) => {
    setSlugEdited(true);
    setSlug(value);
  };

  // In the form, after the title field:
  return (
    // ...
    <div>
      <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
        Slug <span className="font-normal text-slate-400">(optional)</span>
      </label>
      <input
        type="text"
        value={slug}
        onChange={(e) => handleSlugChange(e.target.value)}
        className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm ..."
        placeholder="auto-generated from title"
      />
      {slug && (
        <p className="mt-1 text-xs text-slate-400">
          Filename: <code>change-requests/NNN-{slug}.md</code>
        </p>
      )}
    </div>
    // ...
  );
}
```

Submit: pass `slug: slug || undefined` so that an empty field is treated as "auto-derive from title" on the backend.

### 7. Frontend — `CreatePage.tsx` for bugs (`pages/bugs/CreatePage.tsx`)

Apply the same slug field pattern. Hint text: `Filename: bugs/NNN-{slug}.md`.

---

## Acceptance criteria

- Creating a CR from the UI with no slug set → slug is derived from the title (existing behaviour, no regression).
- Creating a CR from the UI with `slug = "my-custom-name"` → the CR is stored with slug `my-custom-name` and the file syncs as `change-requests/NNN-my-custom-name.md`.
- The slug field auto-fills from the title until the user manually edits it.
- Once the user edits the slug, title changes no longer overwrite it.
- Sending an invalid slug (e.g. `"My Slug!!"`) results in it being sanitised to `my-slug` (backend `slugify`).
- Same behaviour applies to bugs.
- CLI push flow is unaffected (no `explicit_slug` passed, path-based slug extraction still works).
