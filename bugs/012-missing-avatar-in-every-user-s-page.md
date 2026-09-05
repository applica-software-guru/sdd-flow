---
title: Missing avatar in every user's page
status: resolved
author: remote
created-at: '2026-09-05T13:13:10.860000Z'
---
## Summary

Users can have a valid `avatar_url` (for example imported from Google OAuth), and the Profile page renders that image correctly. Everywhere else the same user identity is currently rendered as initials only, so valid profile images are never displayed in operational/collaboration contexts such as authors, assignees, comments and audit-log user cells.

## Reproduction

1. Sign in with a user that has a non-null `avatar_url` (Google `picture` is enough).
2. Open `/settings/profile` and verify that the account section renders the image from `user.avatar_url`.
3. Create or open a project with change requests and bugs where that same user appears as:
   - author in CR/bug list rows;
   - assignee in CR/bug list rows and assignment history;
   - author/assignee in the CR/bug detail assignment panel;
   - comment author in CR/bug comments;
   - user in audit-log rows.
4. Observe that those locations show initials or plain text, not the user's profile image.

## Expected behavior

When a resolved user has a valid `avatar_url`, all shared user renderers must display the image avatar. Initials remain the fallback when `avatar_url` is missing or when the image fails to load. Text truncation and existing tooltips must keep working for long display names/emails.

## Actual behavior

Only `code/frontend/src/pages/system/profile-page.tsx` checks `user?.avatar_url` and renders an `<img>`. Other user identity components receive and render only `display_name`/`email`, so the avatar URL is either missing from the API payload or ignored by the frontend.

## Investigation

### Backend

- `code/backend/app/models/user.py` already stores `avatar_url`.
- `code/backend/app/schemas/auth.py::UserResponse` includes `avatar_url`, which explains why the Profile page works.
- `code/backend/app/schemas/users.py::UserBrief` only exposes `id`, `display_name` and `email`.
- `UserBrief` is embedded in most collaboration responses:
  - `CRResponse.author` / `CRResponse.assignee`;
  - `BugResponse.author` / `BugResponse.assignee`;
  - `CommentResponse.author`;
  - `AssignmentEntryResponse.assignee`;
  - audit-log resolved user data built in `code/backend/app/services/audit.py`.
- `code/backend/app/services/users.py::resolve_user_briefs()` and the local audit-log mapping instantiate `UserBrief` without `avatar_url`, so even clients prepared to render images would not receive the URL.

### Frontend

- `code/frontend/src/types/auth.ts::UserBrief` does not include `avatar_url`.
- `code/frontend/src/components/user-name.tsx` only renders initials; it has no `avatarUrl` prop and no image fallback handling.
- `code/frontend/src/components/user-cell.tsx` passes only `display_name` and `email` to `UserName`.
- `code/frontend/src/components/comment-header.tsx` renders initials directly instead of using the shared user renderer.
- `code/frontend/src/components/assignment-panel.tsx` renders author/assignee/assignment history as plain text, not as avatar-aware identities.
- `code/frontend/src/pages/project/dashboard-page.tsx` renders recent CR/bug authors as text only.

## Root cause

The application has two separate user payload shapes: full `UserResponse` includes `avatar_url`, while the lightweight `UserBrief` used outside the profile area omits it. In addition, the shared identity UI (`UserName`/`UserCell` and comment/assignment/dashboard renderers) only supports initials/text. Therefore valid avatar URLs are lost at the API boundary and never rendered in most pages.

## Proposed fix

1. Extend `code/backend/app/schemas/users.py::UserBrief` with `avatar_url: str | None = None`.
2. Update all `UserBrief` construction paths to include `u.avatar_url`:
   - `code/backend/app/services/users.py::resolve_user_briefs()`;
   - `code/backend/app/services/audit.py` batch mapping.
3. Update `code/frontend/src/types/auth.ts::UserBrief` with optional `avatar_url?: string | null`.
4. Make `code/frontend/src/components/user-name.tsx` avatar-aware:
   - add an `avatarUrl?: string | null` prop;
   - render `<img src={avatarUrl}>` when present;
   - keep initials as fallback, including an `onError` fallback if the image cannot load;
   - preserve `shrink-0`, `min-w-0`, `truncate`, and email `title` behavior.
5. Pass `avatar_url` through `UserCell`, `CommentHeader`, audit-log rows, assignment panel/history, and dashboard recent item authors. Prefer reusing `UserName` where possible to avoid duplicated avatar logic.
6. Add/update tests:
   - backend tests should assert that resolved `author`, `assignee`, comment `author`, assignment history `assignee`, and audit-log `user` include `avatar_url` when present;
   - frontend tests should assert that `UserName`/`UserCell`/`CommentHeader` render an image for `avatar_url` and initials when missing.

## Acceptance criteria

- A Google user with `avatar_url` sees the same image in Profile, comments, CR/bug author cells, assignee cells, assignment panels/history, project dashboard recent items, and audit-log user cells.
- If `avatar_url` is absent or the image fails to load, initials/fallback behavior is unchanged.
- Existing table/detail layouts do not regress: avatars stay `shrink-0`, labels remain truncated, and long emails are tooltips only.
- No N+1 user lookups are introduced; existing batch resolution remains intact.
- Regression tests cover both API payload enrichment and frontend rendering.
