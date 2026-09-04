---
title: "Unified user Profile panel (name, password, notifications) and robust user-name display"
status: applied
author: "user"
created-at: "2026-09-04T00:00:00.000Z"
---

# CR-035: Unified User Profile Panel and Robust User-Name Display

## Summary

Three related improvements around user identity and self-service settings:

1. **Unified "Profile" panel** — a single `/settings/profile` page where every user manages their own account: display name, password (when not a Google-only account), and the existing email notification preferences (moved from the current notifications-only page).
2. **Backend self-service endpoints** — `PATCH /auth/me` to update the own profile and `POST /auth/me/change-password` to change the password after verifying the current one.
3. **Fix user-name/email overflow** — everywhere a user is shown (tables, comment headers, assignment panel, audit log, header menu), long values (emails used as display names) currently overflow onto adjacent elements in tight layouts. Introduce consistent truncation rules and a better display-name fallback for Google users without a name.

## Problem

1. Users cannot manage their own identity: there is no way to change the display name after signup. The only self-service settings page is `/settings/notifications`, which deals exclusively with email notification toggles.
2. Users registered with email & password cannot change their password from the UI (only via the forgot/reset-password email flow). Google-only users cannot manage anything at all.
3. Having notification preferences as a standalone "Settings" entry is misleading — users expect one "Profile" place for personal settings, and more such settings will come over time.
4. When a user has no real name (e.g. Google OAuth users whose `display_name` falls back to their email), the email string is rendered in tight UI slots (table cells, comment headers, tenant member rows, header user menu) and overflows onto adjacent elements, breaking layouts.
5. Even when a name exists, several render sites place `truncate` on a child of a flex container without `min-w-0`, so truncation doesn't actually kick in and the long text pushes siblings out of bounds.

## Goals

1. One Profile page (`/settings/profile`) with: account info (avatar, email read-only, editable display name), security section (change password for password users), and notification preferences (relocated).
2. Backend endpoints to update own display name and change own password safely (current password verification, audit logging).
3. A single consistent pattern for rendering user names across the app that can never overflow its container.
4. Better fallback display name for Google users (derived from the email local part instead of the raw email address), applied at account creation and not retroactively.
5. Full backend, frontend, and e2e regression coverage.

## Non-Goals (Out of Scope)

- Avatar upload (a `avatar_url` field already exists; rendering it where present is in scope, uploading/choosing an image is not).
- Email address change (requires a new verification flow — future CR).
- Account deletion / data export (future CR).
- Two-factor authentication.

## Proposed Solution

### Feature 1 — Backend: self-service profile endpoints

1. **`PATCH /auth/me`** (authenticated):
   - Body: `{ display_name?: string }` (trimmed, 1–80 chars, required non-empty if provided).
   - Only `display_name` is mutable via this endpoint; `email`, `google_id`, `email_verified` are rejected.
   - On success: update `updated_at`, write an audit log entry (`user.profile_updated`, changed fields), and return the updated `UserResponse`.
2. **`POST /auth/me/change-password`** (authenticated):
   - Body: `{ current_password?: string, new_password: string }` (min 8 chars, same policy as registration).
   - Behavior depends on the account type:
     - **Password user** (`password_hash` set): `current_password` is required and must verify against the stored hash; otherwise `400` with a clear detail.
     - **Google-only user** (`password_hash` null): `current_password` is ignored/forbidden; the endpoint **sets** an initial password, enabling hybrid login (Google or password). Respond with `201`-style semantics or a flag in the response (e.g. `{ password_set: true, is_new: true }`) so the UI can show the right message.
   - On success: rehash with bcrypt, revoke **all other refresh tokens** for the user (keep the current session), audit log (`user.password_changed`), fire-and-forget confirmation email reusing the existing mailer.
   - Google-only users with no password: forbid using `POST /auth/me/change-password` for *removal* of password — there is no "unlink Google" in this CR.
3. Both endpoints live in `code/backend/app/api/auth.py`, with request/response schemas in `code/backend/app/schemas/auth.py`, logic in `code/backend/app/services/auth.py` (or a new `profile` service), and validation errors as standard FastAPI `HTTPException` details.
4. Extend the seed-created admin flow unchanged; no data migration needed (fields already exist on `User`).

### Feature 2 — Frontend: unified Profile page

1. New page `code/frontend/src/pages/system/ProfilePage.tsx` mounted at `/settings/profile`, structured in cards/sections:
   - **Account**: avatar (initials circle, or `avatar_url` image when present), email (read-only, with `email_verified` badge when true), display name (inline editable with save button + optimistic update via react-query mutation `useUpdateProfile`, invalidating the `['auth','me']` cache).
   - **Security** (rendered only when the account can use a password, i.e. `password_hash` present **or** the user is Google-only and hasn't set one yet):
     - password users: form with `current password`, `new password`, `confirm new password`; client-side match/length checks, server error surfaced inline.
     - Google-only users: copy explains they currently sign in with Google and can optionally set a password to also log in with email & password; single `new password` + `confirm` form.
     - after success: toast ("Password updated — other sessions have been signed out").
   - **Notification preferences**: the existing per-event-type email toggles (moved verbatim from `NotificationPreferencesPage.tsx`, same labels/defaults — the UI block is relocated, not redesigned).
2. Update the header user menu in `code/frontend/src/components/Layout.tsx`:
   - menu item becomes "Profile" pointing to `/settings/profile` (icon: user silhouette), keeping the notifications link removed from the menu (preferences are inside Profile now).
   - the menu header block (name + email) gets `max-w-full min-w-0` + `truncate` so long emails can't overflow the 48-wide dropdown.
3. Keep `/settings/notifications` as a redirect to `/settings/profile#notifications` for backward compatibility (bookmarks/links), then remove the old page component.
4. New/changed hooks in `code/frontend/src/hooks/useAuth.ts`: `useUpdateProfile`, `useChangePassword`. Types in `code/frontend/src/types/index.ts` extended accordingly (`User` gains nothing new structurally, but add `has_password?: boolean` or reuse `password_hash` presence from `GET /auth/me` — decide at implementation time and keep `UserBrief` unchanged).

### Feature 3 — Fix user-name/email display overflow everywhere

1. **Shared rule**: any element rendering a user name/email inside a flex/grid context must ensure the text can shrink:
   - the text node gets `truncate`;
   - every flex/grid ancestor between the text and the sized container gets `min-w-0`;
   - the avatar keeps `shrink-0`.
2. Introduce a small reusable component `code/frontend/src/components/UserName.tsx` (name + optional inline avatar, `title` tooltip with the email, always `truncate` + `min-w-0`), and use it in:
   - `UserCell.tsx` (refactor to wrap `UserName`) — used in CR/bug tables;
   - `CommentHeader.tsx` — comment author line;
   - `AssignmentPanel.tsx` — author and assignee rows;
   - `AuditLogPage.tsx` — actor cell;
   - `DashboardPage.tsx` — "by {author}" lines (wrap the author name in the truncating span, not the whole sentence);
   - tenant `SettingsPage.tsx` — members table (name + email stacked, each independently truncated);
   - `Layout.tsx` — user menu header.
3. Tight-context policy: in narrow containers (table cells, comment meta) show the **display name** truncated with the email in the `title` tooltip; never render the raw email as visible text in those slots unless there is a dedicated column/row for it (as in the tenant members table).
4. Dark-mode and `aria` attributes preserved; no layout changes to surrounding elements.

### Feature 4 — Better display-name fallback for Google users

1. In the Google OAuth account-creation path (`code/backend/app/services/auth.py`), when Google provides no `name`, derive the display name from the email **local part** (e.g. `mario.rossi@acme.com` → `Mario Rossi` by splitting on `.`, `_`, `-` and title-casing) instead of storing the full email address.
2. Applies only to newly created accounts; existing accounts keep their stored value (users can now fix it themselves via the new Profile panel).
3. `UserCell`, comment headers, etc. keep working unchanged — but with a human-readable name the overflow risk drops dramatically.

## Acceptance Criteria

1. A user can change their display name from `/settings/profile`; the change is reflected immediately in the header menu, comments, tables, and audit log entries created afterwards.
2. A password user can change their password with the current one verified; wrong current password yields an inline error; other sessions are revoked; current session stays alive.
3. A Google-only user sees the security section with the "set a password" flow and, after setting one, can log in with email + password.
4. `/settings/notifications` redirects to the Profile page; notification email toggles work identically inside the Profile page.
5. No user name/email visibly overflows its container in any of the listed render sites, with both short names, long names, and email-length values, at narrow and wide viewport widths.
6. New audit log entries exist for profile update and password change.
7. Backend and frontend test suites cover the new endpoints, the new page interactions, and truncation behavior.

## Test Plan

- **Backend**: extend `code/backend/tests/test_auth.py` (or new `test_profile.py`):
  - `PATCH /auth/me` happy path, empty/too-long `display_name`, unauthenticated;
  - change password: wrong current password, weak new password, Google-only set-password, refresh-token revocation of other sessions, audit entries written.
- **Frontend**: component tests for `ProfilePage` (edit name flow, password forms validation, notification toggles render) and `UserName` truncation (`truncate`/`min-w-0` classes present, no layout jank).
- **E2E/CI**: existing GitHub Actions pipeline runs the new tests automatically (per CR-005).

## Agent Notes

- Reuse the existing bcrypt hashing, refresh-token revocation, mailer, and audit-log services — no new infrastructure.
- All new UI must support light/dark mode and follow the standardized page width (CR-028) via `PageContainer`.
- Keep react-query as the only data layer: mutations must invalidate `['auth','me']` and any affected lists.
- Do not expose `password_hash` or any secret in `UserResponse`; signal "can set password" with a boolean only.
- When applying this CR, update `product/features/auth.md` (self-service profile section) and `product/features/notifications.md` (preferences location), and `system/interfaces.md` with the two new endpoints.