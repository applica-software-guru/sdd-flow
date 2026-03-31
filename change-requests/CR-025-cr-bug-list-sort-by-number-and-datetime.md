---
title: "Sort CR/Bug lists by progressive number desc, show date+time"
status: applied
author: "user"
created-at: "2026-03-31T00:00:00.000Z"
---

## Summary

Two related UX improvements to the Change Request and Bug list views:

1. **Default sort order**: lists must be ordered by progressive number descending (highest number first), so the most recently created items always appear at the top.
2. **Date fields**: all date columns must display both date and time, not date only.

---

## Analysis

### Sorting

The backend currently sorts both lists by `createdAt` descending:

```python
# code/backend/app/api/change_requests.py:81
items = await ChangeRequest.find(query).sort([("createdAt", -1)]).skip(skip).limit(page_size).to_list()

# code/backend/app/api/bugs.py:81
items = await Bug.find(query).sort([("createdAt", -1)]).skip(skip).limit(page_size).to_list()
```

Both `ChangeRequest` and `Bug` models have an integer `number` field (project-scoped, auto-incremented). Sorting by `number desc` is semantically cleaner and more predictable than sorting by timestamp, especially when multiple items are created in rapid succession.

The sort key must change from `("createdAt", -1)` to `("number", -1)`.

### Date formatting

The frontend renders dates using `toLocaleDateString()` on both list pages, which omits the time component:

```typescript
// code/frontend/src/pages/change-requests/ListPage.tsx:145
{new Date(cr.created_at).toLocaleDateString()}

// code/frontend/src/pages/bugs/ListPage.tsx:174
{new Date(bug.created_at).toLocaleDateString()}
```

Must change to `toLocaleString()` to include both date and time.

---

## Required changes

### `product/features/change-requests.md`

In the sorting/filtering section, update:

> Default sort order: progressive number descending (newest first)

### `product/features/bugs.md`

In the sorting/filtering section, update:

> Default sort order: progressive number descending (newest first)

---

### Backend — `code/backend/app/api/change_requests.py`

Change sort key from `createdAt` to `number`:

```python
items = await ChangeRequest.find(query).sort([("number", -1)]).skip(skip).limit(page_size).to_list()
```

### Backend — `code/backend/app/api/bugs.py`

Change sort key from `createdAt` to `number`:

```python
items = await Bug.find(query).sort([("number", -1)]).skip(skip).limit(page_size).to_list()
```

### Frontend — `code/frontend/src/pages/change-requests/ListPage.tsx`

Change date rendering from `toLocaleDateString()` to `toLocaleString()`.

### Frontend — `code/frontend/src/pages/bugs/ListPage.tsx`

Change date rendering from `toLocaleDateString()` to `toLocaleString()`.
