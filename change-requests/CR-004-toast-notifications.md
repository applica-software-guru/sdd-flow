---
title: "Add toast notifications for user actions and save operations"
status: applied
author: roberto
created-at: 2026-03-16T23:15:00Z
---

## Problem

When users perform actions like saving settings, creating a CR, reporting a bug, or deleting an item, there is no visual feedback confirming the action succeeded (or failed). Users have to infer success from page navigation or lack of errors, which is a poor user experience.

## Solution

Implement a toast notification system that displays brief, auto-dismissing messages at the bottom-right of the screen whenever an action completes. Toasts should:

1. **Support multiple variants**: `success` (green), `error` (red), `info` (blue), `warning` (yellow).
2. **Auto-dismiss** after a configurable duration (default 3 seconds).
3. **Allow manual dismiss** by clicking an X button.
4. **Stack vertically** when multiple toasts are active.
5. **Support dark mode** with appropriate `dark:` variant classes.
6. **Show toasts for all user actions**, including:
   - Create/update/delete change requests
   - Create/update/delete bugs
   - Create/update/delete documents
   - Save project settings (name, slug, description)
   - Create/revoke API keys
   - Archive/restore projects
   - Save tenant settings
   - Invite/remove team members
   - Add comments
   - Errors from failed API calls

### Implementation steps

1. Create a `ToastContext` (`src/context/ToastContext.tsx`) that:
   - Maintains an array of active toasts with `id`, `message`, `variant`, and `duration`.
   - Exposes an `addToast(message, variant?, duration?)` function.
   - Auto-removes toasts after their duration expires.
2. Create a `ToastContainer` component (`src/components/ToastContainer.tsx`) that:
   - Renders at the bottom-right of the viewport using `fixed` positioning.
   - Maps over active toasts and renders each with an icon, message, and close button.
   - Uses CSS transitions for enter/exit animations.
3. Wrap the app with `ToastProvider` in `main.tsx`.
4. Render `<ToastContainer />` inside the provider.
5. Add `useToast()` calls in all mutation `onSuccess` and `onError` callbacks across hooks.

## Affected files

### New files
- `code/frontend/src/context/ToastContext.tsx` — Toast state management and provider
- `code/frontend/src/components/ToastContainer.tsx` — Fixed-position toast renderer

### Modified files
- `code/frontend/src/main.tsx` — Wrap app with `ToastProvider`
- `code/frontend/src/hooks/useTenants.ts` — Add toast on create/update tenant, invite/remove member
- `code/frontend/src/hooks/useProjects.ts` — Add toast on create/update/archive project
- `code/frontend/src/hooks/useChangeRequests.ts` — Add toast on create/update/transition CR, add comment
- `code/frontend/src/hooks/useBugs.ts` — Add toast on create/update/transition bug, add comment
- `code/frontend/src/hooks/useDocs.ts` — Add toast on create/update/delete doc
- `code/frontend/src/hooks/useApiKeys.ts` — Add toast on create/revoke API key
