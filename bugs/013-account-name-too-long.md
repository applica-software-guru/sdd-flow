---
title: Account name too long
status: resolved
author: remote
created-at: '2026-09-05T13:33:29.956000Z'
---

## Summary

When a user has no usable display name, the frontend falls back to the user's email address. When either the display name or the fallback email is very long, some user identity surfaces can consume too much horizontal space or become hard to scan. The application needs one consistent frontend strategy for compact user labels: show a safe, bounded visible name, preserve the full value in a tooltip/title, and keep avatars/initials from being affected by long text.

## Reproduction

1. Create or sign in as a user whose `display_name` is missing/empty, so the UI uses the email as the visible label.
2. Use a long email address such as `averyveryveryveryverylongaddress.with.extra.parts@example-very-long-domain-name.test`.
3. Alternatively, set a valid but very long display name, for example `Alexandria Cassandra Montgomery-Worthington Senior Product Operations Administrator`.
4. Open user-heavy frontend areas:
   - the top-right user menu;
   - Profile account header;
   - project dashboard recent CR/bug rows;
   - CR/bug list author and assignee cells;
   - CR/bug detail author, assignee, assignment history and comments;
   - tenant settings member lists and member/invitation tables;
   - audit log user cells and resolved member labels;
   - assign-to dropdowns.
5. Observe whether the label pushes adjacent content, wraps unexpectedly, makes rows taller, or leaves too much of an email visible in compact layouts.

## Expected behavior

- Every user identity shown in compact UI must remain bounded and layout-safe.
- If `display_name` is usable, it is preferred over email.
- If `display_name` is missing or blank, email may be used as fallback, but only as a compact visible label.
- Long display names/emails are truncated or shortened consistently without overflowing containers.
- The full value remains accessible through `title`/tooltip or an equivalent accessible affordance.
- Avatars/initials remain `shrink-0`; only the text part may shrink/truncate.
- Existing avatar rendering from `avatar_url` must keep working.

## Actual behavior / risk

Several identity renderers already use `truncate` and `min-w-0`, but the logic is distributed and not all surfaces use the shared renderer. Some places still render `display_name` directly, use duplicated avatar/name markup, or place full names in `<option>` text where very long values can dominate the control. This makes behavior inconsistent and risks regressions where a long email/display name reintroduces overflow or excessive spacing.

## Investigation

### Shared renderer

- `code/frontend/src/components/user-name.tsx` is the canonical identity renderer.
- It already uses `min-w-0`, `truncate`, a tooltip via `title={email}`, and avatar/image fallback handling.
- Current visible label is `name || email || fallback`; this means a very long display name or fallback email is passed directly to the truncated span. CSS prevents most overflow, but there is no reusable string-shortening rule for compact labels.
- The tooltip currently prefers email; for a very long display name, the full display name is not always exposed if different from email.

### Surfaces already using `UserName` / `UserCell`

- `code/frontend/src/components/user-cell.tsx` delegates to `UserName`.
- Work item tables use `UserCell` in `code/frontend/src/features/work-items/work-item-table.tsx`.
- Project dashboard recent CR/bug rows use `UserName` with a max width.
- `code/frontend/src/components/assignment-panel.tsx` uses `UserName` for author/current assignee/history assignee.
- `code/frontend/src/pages/system/audit-log-page.tsx` uses `UserName` for audit rows.

These areas are mostly protected by CSS truncation, but should inherit a single compact-label policy from `UserName`.

### Duplicated or direct rendering to review

- `code/frontend/src/components/comment-header.tsx` duplicates avatar/name rendering instead of reusing `UserName`; it uses `truncate`, but duplicates fallback and tooltip behavior.
- `code/frontend/src/components/layout/user-menu.tsx` renders `user.display_name` and `user.email` directly. It truncates both, but does not use the shared identity policy and initials are based only on `display_name`.
- `code/frontend/src/pages/system/profile-page.tsx` renders the account header directly and uses email as a separate line; long values are truncated but behavior is local.
- `code/frontend/src/pages/tenant/settings-page.tsx` renders tenant members/invitations directly; display names and emails need the same max-width/truncation/title guarantees.
- `code/frontend/src/features/work-items/create-work-item-form.tsx` and `code/frontend/src/components/assignment-panel.tsx` render member names inside select/options; these cannot be styled like normal spans, so labels should be pre-shortened before being used in options.
- `code/frontend/src/pages/system/audit-log-page.tsx` member filter/list labels render `member.display_name` directly in at least one place.

## Root cause

User label handling is not centralized enough. The frontend has a shared `UserName` component for many compact contexts, but other areas still render raw `display_name`/`email` strings or duplicate the same markup. In addition, there is no shared helper that normalizes blank names and produces a bounded visible label for controls where CSS truncation is insufficient (for example `<option>` text). As a result, long names and email fallbacks are managed case by case.

## Proposed fix

1. Add a small shared formatting helper, for example in `code/frontend/src/utils/user.ts` or `code/frontend/src/lib/format.ts`:
   - `userDisplayLabel(userOrParts, fallback = '--')`: trims `display_name`, falls back to trimmed email, then fallback text;
   - `compactUserLabel(label, max = 32)`: shortens long labels with an ellipsis for contexts that cannot rely on CSS truncation;
   - optionally `userLabelTitle(...)`: returns the full display name/email for tooltip/title.
2. Update `UserName` to use the shared label helper:
   - treat blank display names as missing;
   - keep CSS truncation as the primary layout protection;
   - set `title` to the full visible source value (display name when shown, email when email is shown), not only email;
   - keep the existing `avatarUrl` image fallback and `shrink-0` behavior.
3. Reuse `UserName` where possible instead of duplicated user markup:
   - consider replacing `CommentHeader`'s duplicated avatar/name block with `UserName` plus the timestamp line, or at minimum use the same helper functions;
   - use the helper in `UserMenu`, Profile header, tenant member rows, audit member labels, and any compact direct rendering.
4. For `<select>` / `<option>` labels, use `compactUserLabel(...)` because CSS truncation cannot reliably constrain option text across browsers:
   - assignment panel member options;
   - work item create/assignment controls;
   - any tenant/member picker options.
5. Preserve full values through `title` attributes on visible spans/buttons and do not expose raw long email text where it can overflow.
6. Add or update frontend tests:
   - `UserName` shows display name when present, email fallback when name is blank/missing, and final fallback when both are missing;
   - long labels include `truncate`, keep avatar `shrink-0`, and expose full text via `title`;
   - `compactUserLabel` shortens names/emails over the chosen max length;
   - user menu/comment header/tenant member rows do not render unbounded raw labels.

## Acceptance criteria

- A user with an extremely long `display_name` never breaks layout in user menu, profile header, dashboard rows, CR/bug lists, detail pages, comments, assignment history, tenant settings or audit log.
- A user without a usable display name falls back to email safely without rendering an unbounded long email in compact UI.
- Full names/emails remain available via tooltip/title or equivalent accessible disclosure.
- `UserName` remains the canonical renderer for user identities; duplicated implementations either delegate to it or use the same shared label helpers.
- Avatar images and initials continue to render correctly and remain fixed-size/shrink-safe.
- Select/dropdown option labels are compacted so very long names/emails do not make controls unusable.
- Regression tests cover blank names, long display names, long email fallback, avatar fallback and compact option labels.
