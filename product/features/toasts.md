---
title: "Toast Notifications"
status: new
author: "roberto"
last-modified: "2026-03-16T23:15:00.000Z"
version: "1.0"
---

# Toast Notifications

## Overview

The application displays brief, auto-dismissing toast notifications to provide feedback whenever a user action completes or fails.

## Features

### Variants

- **Success** (green) — action completed successfully
- **Error** (red) — action failed
- **Info** (blue) — informational message
- **Warning** (yellow) — caution or non-critical issue

### Behavior

- Toasts appear at the bottom-right of the viewport
- Auto-dismiss after 3 seconds (configurable per toast)
- Manual dismiss via close (X) button
- Multiple toasts stack vertically
- Supports dark mode

### Triggers

Toasts fire on `onSuccess` and `onError` callbacks for all mutations:

- **Tenants**: create, update settings, invite/remove members
- **Projects**: create, update settings, archive/restore
- **Change Requests**: create, transition status, add comment
- **Bugs**: create, transition status, add comment
- **Documents**: create, update, delete
- **API Keys**: create, revoke

## Implementation

### ToastContext

- File: `src/context/ToastContext.tsx`
- Maintains array of `{ id, message, variant, duration }` toasts
- Exposes `addToast(message, variant?, duration?)` via `useToast()` hook
- Auto-removes toasts after their duration

### ToastContainer

- File: `src/components/ToastContainer.tsx`
- Fixed position bottom-right
- Renders each toast with variant-colored icon, message text, and close button
- Dark mode via `dark:` classes

### Integration

- `ToastProvider` wraps the app in `main.tsx`
- `ToastContainer` rendered inside the provider
- All mutation hooks call `addToast()` in their `onSuccess`/`onError` callbacks
