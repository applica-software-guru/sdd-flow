---
title: "Make doc viewer breadcrumb fully navigable"
status: applied
author: "user"
created-at: "2026-07-16T00:00:00.000Z"
---

## Summary

When viewing a document at a nested path (e.g. `product/features/test.md`), the breadcrumb in the card header shows `Docs > product > features > test.md` but only the `Docs` root link is clickable. The intermediate folder segments (`product`, `features`) are plain text with no navigation. Users cannot jump to an intermediate folder from the document view; they must go back to root and re-navigate the tree manually.

---

## Analysis

### Current implementation

`PathBreadcrumb` in `code/frontend/src/pages/docs/ViewPage.tsx` (lines 12–36) builds the breadcrumb from the document's `path` field:

```typescript
function PathBreadcrumb({ path, docsBase }: { path: string; docsBase: string }) {
  const parts = path.split('/').filter(Boolean);
  return (
    <nav ...>
      <Link to={docsBase}>Docs</Link>   {/* ✓ navigable */}
      {parts.map((part, i) => {
        const isLast = i === parts.length - 1;
        return (
          <span key={i} ...>
            <chevron />
            {isLast
              ? <span className="font-medium ...">{part}</span>   {/* current page — correct */}
              : <span>{part}</span>}                              {/* ✗ should be a link */}
          </span>
        );
      })}
    </nav>
  );
}
```

Intermediate parts are rendered as `<span>` elements. The `TreePage` navigates to sub-folders via the `?path=` query param (e.g. `docsBase?path=product%2Ffeatures`); the same pattern must be applied here.

### Required fix

For each intermediate segment, compute the accumulated folder path up to that position and render a `<Link>` instead of a `<span>`. The last segment (the filename) remains non-interactive, as it represents the current page.

Example for `product/features/test.md`:

| Segment    | Target URL                                    |
|------------|-----------------------------------------------|
| `Docs`     | `/tenants/x/projects/y/docs`                  |
| `product`  | `/tenants/x/projects/y/docs?path=product`     |
| `features` | `/tenants/x/projects/y/docs?path=product%2Ffeatures` |
| `test.md`  | *(plain text — current page)*                 |

---

## Required changes

### `PathBreadcrumb` in `ViewPage`

**File:** `code/frontend/src/pages/docs/ViewPage.tsx`

Replace the intermediate `<span>` with a `<Link>` that points to the accumulated folder path:

```typescript
function PathBreadcrumb({ path, docsBase }: { path: string; docsBase: string }) {
  const parts = path.split('/').filter(Boolean);
  return (
    <nav className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
      <Link to={docsBase} className="hover:text-blue-600 dark:hover:text-blue-400">
        Docs
      </Link>
      {parts.map((part, i) => {
        const isLast = i === parts.length - 1;
        const folderPath = parts.slice(0, i + 1).join('/');
        return (
          <span key={i} className="flex items-center gap-1">
            <svg className="h-3 w-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
            {isLast ? (
              <span className="font-medium text-slate-700 dark:text-slate-200">{part}</span>
            ) : (
              <Link
                to={`${docsBase}?path=${encodeURIComponent(folderPath)}`}
                className="hover:text-blue-600 dark:hover:text-blue-400"
              >
                {part}
              </Link>
            )}
          </span>
        );
      })}
    </nav>
  );
}
```

No other files need to change. The `?path=` query param is already consumed by `TreePage` to filter the document list to the selected folder.

---

## Acceptance criteria

- Viewing a document at `product/features/test.md` shows the breadcrumb `Docs > product > features > test.md`.
- Clicking `Docs` navigates to the docs root.
- Clicking `product` navigates to the docs tree filtered to the `product` folder.
- Clicking `features` navigates to the docs tree filtered to the `product/features` folder.
- `test.md` (last segment) is not clickable.
- The fix works for documents at any depth, including single-level paths (e.g. `system/architecture.md`).
