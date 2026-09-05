---
title: "Authenticated users cannot view the landing page"
status: resolved
author: "roberto"
created-at: "2026-09-05T08:20:38.000Z"
---

## Decisions (review 2026-09-05)

1. `/` remains the public landing page for both anonymous and authenticated visitors.
2. The authenticated navbar CTA is **Open app** and the authenticated hero CTA is **Go to dashboard**.
3. The first iteration shows only the CTA, not the full account menu, in the public navbar.
4. Existing post-login/post-registration navigation and authenticated behavior on `/login` and `/register` remain unchanged; those flows are outside this bug.

## Description

When an authenticated user explicitly navigates to the public frontend root (`/`), the landing page appears only while the authentication request is loading and is then replaced by a redirect to `/tenants`. As a result, logged-in users cannot revisit the product presentation, features, open-source information, or other public landing-page content without logging out.

This behavior is implemented directly in `code/frontend/src/pages/system/landing-page.tsx`:

```tsx
const { data: user, isLoading } = useCurrentUser();

if (!isLoading && user) {
  return <Navigate to="/tenants" replace />;
}
```

The redirect is technically intentional, but it conflates two different destinations:

- `/` as the public product/marketing site;
- `/tenants` as the authenticated application entry point.

It also creates an avoidable visual transition: the landing page is rendered while `/auth/me` is pending, then disappears as soon as the current user is resolved.

## Current behavior

1. A user signs in and has a valid session.
2. The user navigates explicitly to `/`, including by entering the URL or following an external link.
3. The landing page renders briefly while `useCurrentUser()` is loading.
4. The router replaces `/` with `/tenants`.
5. The user cannot view the landing page while authenticated.

## Expected behavior

The public landing page should remain intentionally accessible regardless of authentication state. Authentication should influence its calls to action, but should not silently replace the page the user requested.

A logged-in visitor should see the same public content with session-aware navigation, for example:

- replace **Log in** and **Sign Up** with **Open app** or **Go to dashboard**;
- optionally show the authenticated user's avatar/menu;
- make the primary hero CTA open `/tenants`;
- keep public anchors such as Features, How it Works, For Teams, and Open Source available.

Explicit authentication flows may still navigate to `/tenants` after a successful login or registration. The issue is specifically the unconditional redirect when an authenticated user deliberately requests `/`.

## Options considered

### Option A — Keep `/` public and make the landing page authentication-aware (recommended)

Remove the authenticated-user `<Navigate>` from `LandingPage`. Continue resolving the current user, but use the result only to adapt the landing navigation and CTA controls.

**Advantages**

- Matches the URL the user explicitly requested.
- Minimal routing and backend impact.
- Preserves the existing public URL and SEO behavior.
- Gives authenticated users a clear, deliberate path back into the platform.
- Eliminates the landing-page-to-platform redirect flash.

**Trade-offs**

- `LandingNavbar` and possibly `HeroSection` need an authenticated variant.
- The auth request must not cause buttons to shift noticeably when it resolves; CTA space should remain stable or use a small neutral loading state.

### Option B — Separate the public site and application namespaces

Keep `/` as the public landing page and introduce an explicit application entry route such as `/app`, which redirects or resolves to `/tenants`. Authentication flows would navigate to `/app` or `/tenants`.

**Advantages**

- Strong conceptual separation between marketing and application routes.
- Scales well if the public website and authenticated platform diverge further.

**Trade-offs**

- Larger routing and documentation change.
- Existing links, redirects, tests, and bookmarks need review.
- `/app` adds limited value while `/tenants` already acts as the application entry point.

### Option C — Keep the automatic redirect but add a way to bypass it

Use a query parameter or secondary route, such as `/?stay=true` or `/about`, to allow authenticated users to see public content.

**Advantages**

- Preserves the current root redirect.

**Trade-offs**

- Hidden and difficult to discover.
- Produces two URLs for the same public content.
- Does not respect the normal expectation that explicitly navigating to `/` displays `/`.
- Adds complexity without improving the information architecture.

This option is not recommended.

## Recommended solution

Adopt **Option A**:

1. Treat `/` as a public route for both anonymous and authenticated visitors.
2. Remove the `<Navigate to="/tenants" replace />` branch from `LandingPage`.
3. Pass authentication state to `LandingNavbar` and the hero CTA, or let those components consume a small shared landing-session abstraction.
4. While authentication is unresolved, reserve the CTA area without rendering a misleading redirect or causing layout shift.
5. For authenticated users:
   - show **Open app** linking to `/tenants`;
   - hide **Log in** and **Sign Up**;
   - optionally expose the existing accessible user menu if doing so does not couple the public shell to the full application layout.
6. Keep the post-login and post-registration destination as `/tenants`; this remains an explicit result of completing authentication, not a side effect of visiting the public site.
7. Preserve direct links to protected routes and their existing authentication guard behavior.

The first implementation should prefer the simple **Open app** CTA over embedding the full application user menu. The latter can be considered separately if the public navbar needs account management.

## Affected code

| File | Relevance |
|---|---|
| `code/frontend/src/pages/system/landing-page.tsx` | Contains the unconditional authenticated-user redirect |
| `code/frontend/src/components/landing/landing-navbar.tsx` | Currently always renders Log in and Sign Up actions |
| `code/frontend/src/components/landing/hero-section.tsx` | Primary CTA may need an authenticated Open app variant |
| `code/frontend/src/hooks/use-auth.ts` | Provides current-user state; API behavior should not need to change |
| `code/frontend/src/app.tsx` | Defines `/` and protected application routes; likely no structural change for Option A |
| `code/frontend/e2e/` | Needs coverage for authenticated and unauthenticated visits to `/` |
| `product/features/auth.md` or a landing-page feature document | Should document the final navigation decision when implemented |

## Acceptance criteria for the eventual fix

- An unauthenticated visitor to `/` sees the landing page with Log in and Sign Up actions.
- An authenticated visitor to `/` remains on `/` and can read the complete landing page.
- An authenticated visitor sees an explicit **Open app** or **Go to dashboard** action linking to `/tenants` instead of Log in and Sign Up.
- Completing login or registration still sends the user to the authenticated platform.
- Direct protected-route navigation continues to use the existing authentication guard.
- Resolving `/auth/me` does not replace the landing page, flash the platform, or cause a significant navbar/hero layout shift.
- Keyboard navigation, focus states, dark mode, mobile navigation, and responsive behavior remain correct for both authentication states.
- Playwright covers at least:
  - anonymous visit to `/`;
  - authenticated visit to `/` without redirect;
  - authenticated **Open app** navigation to `/tenants`.

## Decisions required before implementation

1. Confirm that `/` must always remain the public landing page (**recommended: yes**).
2. Confirm the authenticated CTA wording: **Open app** versus **Go to dashboard** (**recommended: Open app** in the navbar, **Go to dashboard** in the hero).
3. Decide whether the public navbar should show only the Open app CTA or also the account menu (**recommended for first iteration: CTA only**).
4. Confirm whether authenticated visits to `/login` and `/register` should keep their current behavior or redirect to `/tenants`; this is related but should not block fixing `/`.
