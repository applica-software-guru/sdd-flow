---
title: "Resolve doc links in CR and bug markdown bodies"
status: applied
author: "user"
created-at: "2026-07-16T00:00:00.000Z"
---

## Summary

When a CR or bug body contains markdown links pointing to project documentation files (e.g. `[See architecture](../system/architecture.md)`), those links do not work in the web application. Clicking them produces a broken URL, making cross-references between CRs/bugs and documentation inaccessible to product and functional team members who rely on the web UI.

The same links work correctly in VS Code because the editor resolves relative paths from the source file's location on disk. The web app has no equivalent resolution logic.

---

## Analysis

### How cross-doc links are written

CRs and bugs live under `change-requests/` and `bugs/` respectively. When a CR author links to a documentation file, they use a relative path from that directory:

```markdown
[`product/features/media-library.md`](../product/features/media-library.md)
[`system/entities.md`](../system/entities.md)
```

This pattern is consistent across all CRs in projects built on SDD (100% of observed cross-doc links use the `../product/` or `../system/` prefix).

### Why links break in the web app

The frontend renders CR and bug bodies through the `MarkdownRenderer` component (`code/frontend/src/components/MarkdownRenderer.tsx`), which uses `react-markdown`. The component's `<a>` handler currently only distinguishes between external links (opened in `_blank`) and internal links (followed in the same window):

```typescript
// MarkdownRenderer.tsx — current link handler
a({ href, children, ...props }) {
  const target = href && isExternalLink(href) ? '_blank' : undefined;
  return <a href={href} target={target} rel={...} {...props}>{children}</a>;
}
```

When the browser renders `href="../product/features/media-library.md"` while on `/tenants/x/projects/y/crs/123`, it resolves the relative URL against the current page, producing `/tenants/x/projects/y/product/features/media-library.md` — a route that doesn't exist in the SPA.

### What is needed to resolve links correctly

To navigate to the correct page, the renderer needs to:

1. Detect that a link is a relative `.md` path (not an external URL).
2. Resolve the relative path against the virtual base path of the entity being rendered:
   - CRs → base path `change-requests`
   - Bugs → base path `bugs`
3. Look up the resolved path (e.g. `product/features/media-library.md`) in the list of project documents to obtain the document's database ID.
4. Navigate to the document viewer route: `/tenants/{tenantId}/projects/{projectId}/docs/{docId}`.

The `useDocs` hook (`code/frontend/src/hooks/useDocs.ts`) already fetches the full list of documents including their `id` and `path` fields, so no new backend endpoint is needed.

---

## Required changes

### `MarkdownRenderer` component

**File:** `code/frontend/src/components/MarkdownRenderer.tsx`

Extend the component's props interface with three optional fields:

```typescript
interface MarkdownRendererProps {
  content: string;
  basePath?: string;                             // "change-requests" or "bugs"
  docs?: Array<{ id: string; path: string }>;    // project documents list
  docsRouteBase?: string;                        // "/tenants/x/projects/y/docs"
}
```

Add a path resolution utility:

```typescript
function resolveDocPath(basePath: string, href: string): string {
  // Use the URL API to correctly handle "../" segments.
  // Example: basePath="change-requests", href="../product/features/foo.md"
  // → "product/features/foo.md"
  const resolved = new URL(href, `fake://h/${basePath}/x.md`).pathname;
  return resolved.replace(/^\//, '');
}
```

Update the `<a>` component to intercept relative `.md` links when doc context is available:

```typescript
a({ href, children, node: _node, ...props }) {
  if (href && basePath && docs && docsRouteBase && !isExternalLink(href) && href.endsWith('.md')) {
    const resolvedPath = resolveDocPath(basePath, href);
    const doc = docs.find(d => d.path === resolvedPath);
    if (doc) {
      return (
        <Link to={`${docsRouteBase}/${doc.id}`}>
          {children}
        </Link>
      );
    }
  }
  // Existing fallback behaviour — external links open in _blank, others in-page
  const target = href && isExternalLink(href) ? '_blank' : undefined;
  const rel = target ? 'noreferrer noopener' : undefined;
  return <a href={href} target={target} rel={rel} {...props}>{children}</a>;
}
```

Import `Link` from `react-router-dom` (already available in the project).

If the document is not found in the list (broken reference), the link falls back to the existing `<a>` behaviour silently — no error is thrown.

---

### CR detail page

**File:** `code/frontend/src/pages/change-requests/DetailPage.tsx`

Add the `useDocs` hook and compute the docs route base:

```typescript
import { useDocs } from '../../hooks/useDocs';

const { data: docs } = useDocs(tenantId, projectId);
const docsRouteBase = `/tenants/${tenantId}/projects/${projectId}/docs`;
```

Pass the new props to every `<MarkdownRenderer>` on the page (both the CR body and the comments list):

```typescript
<MarkdownRenderer
  content={cr.body}
  basePath="change-requests"
  docs={docs}
  docsRouteBase={docsRouteBase}
/>

// and inside comments.map():
<MarkdownRenderer
  content={comment.body}
  basePath="change-requests"
  docs={docs}
  docsRouteBase={docsRouteBase}
/>
```

---

### Bug detail page

**File:** `code/frontend/src/pages/bugs/DetailPage.tsx`

Same pattern as the CR detail page, with `basePath="bugs"`:

```typescript
import { useDocs } from '../../hooks/useDocs';

const { data: docs } = useDocs(tenantId, projectId);
const docsRouteBase = `/tenants/${tenantId}/projects/${projectId}/docs`;

<MarkdownRenderer
  content={bug.body}
  basePath="bugs"
  docs={docs}
  docsRouteBase={docsRouteBase}
/>

// and inside comments.map():
<MarkdownRenderer
  content={comment.body}
  basePath="bugs"
  docs={docs}
  docsRouteBase={docsRouteBase}
/>
```

---

## Acceptance criteria

- A link like `[See entities](../system/entities.md)` in a CR body renders as a clickable link that navigates to the correct document viewer page within the SPA.
- The same fix applies to bug bodies and to comments in both CR and bug detail pages.
- External links (http/https) continue to open in a new tab.
- Markdown links that do not end in `.md` (e.g. plain URLs, anchors) are unaffected.
- A link pointing to a non-existent document renders as a plain `<a>` tag without throwing an error.
- No new backend endpoints are required.
