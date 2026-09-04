---
title: "Scroll-to-comments floating button and email notifications for comments and content changes"
status: applied
author: "user"
created-at: "2026-07-17T00:00:00.000Z"
---

# CR-033: Scroll-to-Comments Floating Button and Email Notifications

## Summary

Three related improvements to the CR/bug collaboration experience:

1. **Scroll-to-comments floating button** — when a CR or bug page is long, a floating action button (FAB) lets the user jump straight to the comments section with one click, instead of manually scrolling to the bottom.
2. **Email notification on new comment** — when a comment is added to a CR or bug, every actor involved in that item (author, assignee, previous commenters) receives an email notification with a deep link to the item.
3. **Opt-in email notification on content change** — users can enable per-item-type email notifications for edits to the body/title of a CR or bug they are involved in.

## Problem

1. CRs and bugs are long documents (markdown body, activity log, assignment history, comments). The comments section sits at the bottom of the detail page, so on long items users must scroll through the entire document to read or write a comment. There is no shortcut.
2. When someone adds a comment, the other involved actors have no way to know unless they happen to revisit the page. In-app notifications exist, but email is the channel that reliably reaches people who are not actively using the app.
3. When a CR/bug body is edited after creation, involved actors are never informed about what changed, even though the change may be substantial (new requirements, updated reproduction steps).

## Goals

1. One-click access to the comments section from anywhere on a CR/bug detail page.
2. All actors involved in a CR/bug are reliably informed by email when a new comment is added.
3. Content edits to CRs/bugs can trigger email notifications, strictly opt-in per user.
4. Reuse the existing mailer, notification, and audit-log infrastructure — no new delivery mechanisms.
5. Full backend, frontend, and e2e regression coverage.

## Definitions

**Actors of a CR/bug**: the union of

- the item **author**,
- the current **assignee** (if any),
- all **distinct users who commented** on the item (comment history),

excluding the user who triggered the event (comment author or editor) and excluding non-active tenant members.

## Proposed Solution

### Feature 1 — Scroll-to-comments floating button (frontend)

1. Add an anchor `id="comments"` to the comments section of both detail pages
   (`code/frontend/src/pages/change-requests/DetailPage.tsx`, `code/frontend/src/pages/bugs/DetailPage.tsx`).
2. New component `code/frontend/src/components/ScrollToCommentsButton.tsx`:
   - fixed-position FAB at the bottom-right of the viewport (above the toast container zone), visible only while the comments section is **below the fold**;
   - uses an `IntersectionObserver` on the comments section to show/hide itself (hidden when the section is already at least partially visible);
   - shows a badge with the comment count (e.g. `💬 3`);
   - on click, performs a smooth scroll to the comments section and focuses the comment input;
   - supports dark mode (`dark:` variants) and is accessible (`aria-label="Scroll to comments"`).
3. Mount the FAB on both detail pages; it renders nothing when there is no comments section (never the case here) and degrades gracefully if JS observers are unavailable (button simply always visible).

### Feature 2 — Email notification on new comment (backend)

1. New event type `comment_added`.
2. In the comment creation endpoint, after persisting the comment:
   - resolve the **actors** of the item (see Definitions);
   - for each actor, create the in-app `Notification` (event type `comment_added`) — reusing `services/notifications.py`;
   - for each actor with an enabled email preference for `comment_added`, send an email.
3. Email defaults: `comment_added` email notifications are **enabled by default** (comments are conversational; this matches the requirement "notify all involved actors"). Users can disable it per event type in their profile settings.
4. Email template (extends `services/email_templates.py`):
   - subject: `[<project name>] <CR|Bug> #<formatted_number> — new comment by <author display name>`;
   - body: item title, comment author, comment body rendered as plain text (markdown stripped, truncated to ~500 chars), deep link to the item (`FRONTEND_BASE_URL` + item route + `#comments` anchor so the email link lands directly on the comments section);
   - reuse the existing mailer abstraction (`services/mailer.py`), including the log-only dev mode.
5. Coalescing: if the same actor already received a `comment_added` email for the same item within the last 5 minutes, batch subsequent comments into one follow-up email (consistent with the batching rule in `product/features/notifications.md`).
6. Failures in notification/email dispatch must never fail the comment creation (fire-and-forget with error logging), mirroring how invitation emails behave.

### Feature 3 — Opt-in email notification on content change (backend + frontend)

1. New event type `content_changed`, triggered when the **body** or **title** of a CR/bug is actually modified (no-op saves that leave content identical must not trigger anything).
2. On update, the backend compares old vs new title/body; if changed:
   - in-app `Notification` (event type `content_changed`) for all actors;
   - email **only** for actors who explicitly enabled the `content_changed` email preference (default: **off** — strictly opt-in);
   - email includes item number/title, who edited, which fields changed (title and/or body), and a deep link to the item.
3. The change is also recorded in the audit log as `cr.content_changed` / `bug.content_changed` (details: which fields changed).
4. Notification preferences UI:
   - complete/extend the per-event-type email toggles in profile settings for the event types `assigned`, `status_changed`, `mentioned`, `comment_added` (default on), `content_changed` (default off);
   - back the UI with a preferences endpoint (see Required Changes).

## Required Changes

### Backend

1. `code/backend/app/api/comments.py` (or the router handling comment creation)
   - after comment creation, dispatch `comment_added` notifications/emails to actors.
2. `code/backend/app/api/change_requests.py`, `code/backend/app/api/bugs.py`
   - detect real content changes on update; dispatch `content_changed` notifications/emails and audit entries.
3. `code/backend/app/services/notifications.py`
   - add `resolve_actors(entity_type, entity_id)` helper (author + assignee + commenters, excluding trigger user and inactive members);
   - add dispatch functions for `comment_added` and `content_changed`.
4. `code/backend/app/services/email_templates.py`
   - add `comment_added` and `content_changed` templates.
5. `code/backend/app/services/notification_preferences.py` (or extend users service)
   - CRUD for `NotificationPreference` per event type with documented defaults.
6. `code/backend/app/config.py` — no new vars expected (reuses mail + `FRONTEND_BASE_URL`); verify deep-link building for CR/bug routes.

### Frontend

1. `code/frontend/src/components/ScrollToCommentsButton.tsx` (new) — the FAB.
2. `code/frontend/src/pages/change-requests/DetailPage.tsx`, `code/frontend/src/pages/bugs/DetailPage.tsx`
   - add `id="comments"` anchor and mount the FAB.
3. Profile / notification settings UI
   - per-event-type email toggles for the five event types with correct defaults.
4. `code/frontend/src/hooks/` — hook for reading/updating notification preferences.

### Documentation

1. `product/features/change-requests.md` — describe the scroll-to-comments button and comment/content-change notifications in the CR detail view section.
2. `product/features/bugs.md` — same additions for the bug detail view.
3. `product/features/notifications.md` — add `comment_added` and `content_changed` event types, their defaults, and the coalescing rule.
4. `system/entities.md` — extend the `Notification.event_type` and `NotificationPreference.event_type` enumerations.
5. `system/interfaces.md` — document the notification preferences endpoints and note the notification side effects of the comment/create and CR/bug update endpoints.

## Testing Strategy

### Backend (pytest)

1. `test_comment_notifies_actors` — author, assignee, and previous commenters each get an in-app notification; the comment author does not.
2. `test_comment_email_sent_to_actors_with_preference_enabled` — mock mailer, assert one send per eligible actor with correct deep link and `#comments` anchor.
3. `test_comment_email_skipped_when_preference_disabled`.
4. `test_comment_email_coalesced_within_window` — two comments within 5 minutes produce one email.
5. `test_comment_failure_does_not_break_comment_creation` — mailer raising does not fail the API call.
6. `test_content_change_triggers_notification_only_on_real_change` — identical body update triggers nothing; title change triggers `content_changed`.
7. `test_content_changed_email_only_optin` — default-off preference means no email unless enabled.
8. `test_audit_entries_recorded` — `cr.commented`/`bug.commented` and `cr.content_changed`/`bug.content_changed` present with correct details.
9. `test_inactive_members_excluded_from_actors`.

### Frontend (vitest)

1. `ScrollToCommentsButton` — hidden when comments visible, visible when below the fold, badge shows count, click scrolls smoothly.
2. Detail pages render the anchor and the FAB.
3. Preferences UI — toggles persist per event type; defaults rendered correctly (`comment_added` on, `content_changed` off).

### E2E (playwright)

1. Open a long CR, click the FAB, land on the comments section, post a comment.
2. User A comments on a bug authored by User B (assigned to User C): B and C receive the email (assert via mail catch-all in dev mode).
3. User disables `comment_added` email → no email on next comment; enables `content_changed` → receives email after an edit.

## Acceptance Criteria

1. On any CR/bug detail page longer than one viewport, a floating button is visible and scrolls directly to the comments; it disappears once comments are in view.
2. Adding a comment notifies (in-app) all actors and emails all actors with `comment_added` enabled (default on), excluding the comment author.
3. Editing a CR/bug title/body notifies all actors in-app; emails go only to users who opted in to `content_changed`.
4. No-op saves generate no notifications.
5. Notification/email failures never break the triggering action.
6. Users can toggle email preferences per event type from profile settings.
7. All listed tests pass; docs updated and consistent.

## Risks and Mitigations

1. **Risk**: email spam on very active items.
   - Mitigation: 5-minute coalescing window per (actor, item); users can disable `comment_added` emails.
2. **Risk**: actor resolution becomes expensive on items with many comments.
   - Mitigation: distinct query on comments by `entity_id` with compound index `(entity_type, entity_id)`; resolve actors once per event, not per recipient.
3. **Risk**: noisy `content_changed` notifications from trivial edits (typos, whitespace).
   - Mitigation: compare normalized content (trimmed); event is opt-in for email by default.
4. **Risk**: deep link lands mid-page and misses context.
   - Mitigation: link to the item route with the `#comments` anchor so the page opens at the comments with full context above.

## Rollout Plan

1. Ship Feature 1 (FAB) — pure frontend, low risk.
2. Ship notification preferences endpoints + UI.
3. Ship Feature 2 (comment emails) behind existing mail config; verify in dev log-only mode first.
4. Ship Feature 3 (content-change notifications).
5. Enable production mail and announce the behavior change ("comment emails are on by default") in release notes.
