---
title: "Installable PWA desktop app"
status: applied
author: "user"
created-at: "2026-09-05T13:55:07.000Z"
---

# CR-043: Installable PWA Desktop App

## Summary

Make the SDD Flow frontend installable as a Progressive Web App (PWA), so users can install it from supported desktop browsers and launch it from the operating-system app launcher/taskbar as if it were a local desktop app.

A production-grade installability baseline requires a complete web app manifest, dedicated desktop/mobile launcher icons, install metadata in `index.html`, and a service-worker strategy that is safe for an authenticated server-backed application.

SDD Flow currently has a basic `public/site.webmanifest` linked from `index.html`, but it is not a complete installable-app plan: it only declares one SVG icon, does not define `id`, `start_url`, `scope`, or description, and has no service worker / asset-caching strategy. The target is to close that gap deliberately while preserving the existing web deployment model.

## User need

As an SDD Flow user, I want to install the web app on my PC and open it directly from my desktop environment, taskbar, dock, or application launcher, so that it behaves like a focused product workspace instead of just another browser tab.

## Product decisions

### Installability target

The first release targets standards-based PWA installation from modern desktop browsers, especially Chromium-based browsers. The app must be installable without packaging a native shell such as Electron or Tauri.

Installed behaviour must use:

- standalone display mode;
- the SDD Flow name and icon in browser install prompts and OS launchers;
- the normal authenticated application routes after launch;
- the same backend/API contracts and deployment topology as the browser version.

### Offline behaviour

SDD Flow is a collaborative, authenticated, server-backed product. This CR does **not** turn it into an offline-first editor.

The PWA must provide a resilient application shell, but server data remains network-dependent:

- static frontend assets may be precached;
- navigation to app routes may fall back to `index.html` so deep links keep working;
- API, auth, websocket, worker, and notification requests must remain network-first or network-only and must not be silently served from stale protected caches;
- when the network is unavailable, the UI must show an understandable offline/error state rather than pretending mutations or sync operations succeeded.

### Updates

Because SDD Flow can be installed and kept open for long sessions, users must not be trapped on stale frontend code indefinitely. The implementation must include an explicit update strategy:

- detect when a new service worker/app version is available;
- notify the user with an accessible toast/banner/dialog;
- allow reloading to activate the new version;
- avoid surprise reloads while the user is editing forms, documents, CRs, bugs, or comments.

## Current-state audit

The current SDD Flow frontend has:

- `code/frontend/index.html` with `<link rel="manifest" href="/site.webmanifest" />` and a theme-colour script;
- `code/frontend/public/site.webmanifest` with `name`, `short_name`, one SVG icon, `theme_color`, `background_color`, and `display: "standalone"`;
- `code/frontend/public/favicon.svg` as the only declared icon source;
- no service worker registration;
- no `vite-plugin-pwa` or equivalent Workbox setup;
- no install/update UX;
- no automated verification of manifest quality, icon sizes, or PWA installability.

SDD Flow is missing the production-grade manifest identity and icon set needed for reliable desktop installation prompts, plus the service-worker layer commonly required by browsers for installability.

## Target design

### Manifest and metadata

Replace or rename the current basic manifest with a production manifest suitable for desktop PWA installation. The final public manifest should be linked from `index.html` and contain at least:

```json
{
  "id": "./",
  "name": "SDD Flow",
  "short_name": "SDD Flow",
  "description": "SDD Flow — Story Driven Development workspace",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "background_color": "#020617",
  "theme_color": "#2563eb",
  "icons": []
}
```

The final colours should respect the current SDD Flow visual identity and dark/light theme behaviour. If the manifest remains named `site.webmanifest`, document that name; if it is renamed to `manifest.webmanifest`, update all references atomically.

`index.html` must also provide complete install metadata:

- manifest link;
- favicon link;
- Apple touch icon link;
- description meta tag;
- theme-colour meta tag compatible with the existing light/dark theme bootstrap;
- any required mobile-web-app / apple-mobile-web-app metadata if useful, without compromising desktop focus.

### Icons

Add a proper icon set under `code/frontend/public/icons/sdd-flow/`:

```text
public/icons/sdd-flow/
├── apple-touch-icon.png      # 180x180
├── rounded-192.png           # 192x192, purpose any
├── rounded-512.png           # 512x512, purpose any
├── maskable-192.png          # 192x192, purpose maskable
└── maskable-512.png          # 512x512, purpose maskable
```

The generated icons must be based on the SDD Flow brand mark, keep safe padding for maskable icons, and render clearly on desktop launchers, Windows taskbar, macOS Dock, and browser install prompts. The existing SVG favicon may remain for browser tabs, but it must not be the only manifest icon.

Add a repeatable generation/check workflow where practical, for example a documented script that generates PNGs from the source SVG or verifies dimensions and manifest references.

### Service worker and caching

Add a PWA service worker using `vite-plugin-pwa` with Workbox unless a better documented alternative is chosen during implementation.

The recommended setup is:

- generate the service worker during `vite build`;
- precache hashed build assets and the application shell;
- use SPA navigation fallback for frontend routes;
- exclude `/api`, `/auth`, websocket endpoints, remote-worker endpoints, and other backend calls from offline/stale caching;
- avoid caching authenticated API responses by default;
- keep cache names/versioning deterministic and easy to invalidate across deployments;
- ensure local `vite dev` remains simple and does not mask service-worker bugs with stale dev caches.

If a runtime cache is added for safe public/static resources, it must be explicitly scoped and justified.

### Registration and UX

Register the service worker from the React entry point or a small PWA module, not through ad-hoc inline code. The registration should expose product-level UX hooks for:

- installability availability, if the browser exposes it;
- app-installed state, where available;
- offline/online status;
- update available / refresh to update.

Add shared UI that fits the current design system and i18n setup:

- accessible update notification with translated English/Italian copy;
- optional install prompt CTA only where browsers allow `beforeinstallprompt`;
- clear offline banner/toast when network connectivity is lost;
- no intrusive prompts on every page load.

The installed app should not lose existing theme or language choices. Theme colour should remain coherent with the active theme, while manifest-level colours provide safe defaults for install surfaces.

## Implementation plan

### Phase 1 — Audit and target definition

1. Record the current SDD Flow manifest, icons, `index.html` metadata, and build output.
2. Compare the current implementation against the PWA installability requirements in this CR.
3. Decide whether to keep `site.webmanifest` or rename to `manifest.webmanifest`; document the decision.
4. Define the final app identity values: name, short name, description, theme colour, background colour, start URL, scope, and display mode.

### Phase 2 — Manifest and icons

5. Create the SDD Flow PNG icon set: rounded 192/512, maskable 192/512, and Apple touch icon.
6. Update the manifest to include `id`, `start_url`, `scope`, `description`, `display`, colours, and all required icons with correct paths and purposes.
7. Update `index.html` metadata and ensure theme-colour handling remains compatible with light/dark mode.
8. Add validation for manifest JSON, icon paths, icon dimensions, and required PWA fields.

### Phase 3 — Service worker foundation

9. Add `vite-plugin-pwa` and configure it in `vite.config.ts` for production builds.
10. Precache the Vite build assets and configure navigation fallback for SPA routes.
11. Explicitly prevent protected backend/API/auth/websocket traffic from being served from stale caches.
12. Document local development guidance for unregistering old service workers and avoiding stale caches during debugging.

### Phase 4 — Install, offline, and update UX

13. Add a small PWA registration module and typed state/hooks for online/offline and update availability.
14. Add an accessible translated update prompt that lets users reload when a new version is ready.
15. Add a non-intrusive offline indicator that explains that server-backed data and mutations require connectivity.
16. Optionally add an install CTA only when the browser exposes a safe install prompt event; otherwise rely on browser install UI.
17. Verify that installed-mode launch preserves routing, authentication refresh, theme, language, and workspace selection.

### Phase 5 — Verification and documentation

18. Run Lighthouse/PWA checks or equivalent automated audits on the production build.
19. Add unit/component tests for the PWA hooks and update/offline UI.
20. Add a Playwright smoke test for manifest availability, service-worker registration in production preview, and deep-link reload behaviour.
21. Update product and system documentation with installability, service-worker boundaries, caching policy, update UX, and desktop support expectations.
22. Run `npm run check`, production build, relevant Playwright suites, and `sdd validate`.

## Documentation changes to apply

When this CR is applied:

- create `product/features/installable-pwa.md` documenting:
  - desktop installability goals;
  - supported browser expectations;
  - standalone launch behaviour;
  - app identity and icons;
  - offline limitations;
  - update notification behaviour;
  - user-facing install guidance;
- update `system/architecture.md` documenting:
  - PWA service-worker registration;
  - precache/navigation-fallback strategy;
  - explicit non-caching policy for API/auth/websocket/protected data;
  - update lifecycle and user-triggered reload;
  - interaction with theme, i18n, auth, and routing;
- update `system/tech-stack.md` adding:
  - `vite-plugin-pwa` / Workbox and their purpose;
  - any icon-generation or manifest-validation tooling introduced;
- update `system/ci-pipeline.md` adding:
  - manifest/icon validation;
  - production build PWA checks;
  - any Lighthouse/PWA smoke gate selected for CI;
- update `product/features/theme.md` only if theme-colour behaviour changes materially;
- update `product/features/localization.md` only to mention translated PWA install/update/offline messages.

## Out of scope

- Electron, Tauri, native installers, MSI/DMG packaging, or app-store distribution;
- offline-first document editing or queued offline mutations;
- caching authenticated API responses for offline reading;
- push notifications;
- background sync;
- changing backend authentication/session semantics;
- changing public URLs, tenant/project routing, or API contracts;
- redesigning the SDD Flow brand beyond generating production-ready PWA icons.

## Acceptance criteria

1. The frontend has a complete web app manifest with `id`, `name`, `short_name`, `description`, `start_url`, `scope`, `display: "standalone"`, `theme_color`, `background_color`, and a valid icon set.
2. Manifest icons include at least 192x192 and 512x512 PNG icons for normal use and maskable 192x192 and 512x512 PNG icons for adaptive launchers.
3. `index.html` links the manifest and app icons and exposes coherent description/theme metadata.
4. A production service worker is generated and registered for built deployments.
5. Static build assets and the SPA application shell are cached safely; authenticated API/auth/websocket traffic is not served from stale caches.
6. Deep links continue to work when the installed app is launched or refreshed.
7. Supported desktop browsers offer SDD Flow as installable when served over HTTPS or localhost.
8. Installed-mode launch opens SDD Flow in standalone mode with correct app name and icon.
9. Existing authentication, refresh-token, tenant/project workspace, theme, and language behaviours continue to work in browser and installed modes.
10. Users receive an accessible, translated notification when a new app version is available and can choose when to reload.
11. Users receive a clear translated offline indication; failed network-dependent operations are not presented as successful.
12. Service-worker updates do not unexpectedly wipe unsaved edits or force reloads during active work.
13. Local development documentation explains how to avoid or clear stale service workers.
14. Automated checks validate manifest structure, icon existence/dimensions, service-worker build output, and critical PWA installability requirements.
15. Unit/component tests cover PWA state and update/offline UI; Playwright or equivalent smoke tests cover production preview registration and route fallback.
16. `npm run check`, production build, selected PWA audits, and `sdd validate` pass.
17. `product/features/installable-pwa.md`, `system/architecture.md`, `system/tech-stack.md`, `system/ci-pipeline.md`, and any necessary theme/localization notes reflect the implemented behaviour.

## Risks and mitigations

- **Stale authenticated data shown from cache:** keep API/auth/websocket requests network-only unless a later CR defines an explicit secure offline-read model.
- **Users stuck on old installed code:** provide update detection and user-triggered reload UX.
- **Service-worker bugs during development:** document unregister/clear-cache steps and keep dev registration disabled or clearly controlled.
- **Install prompt unavailable in some browsers:** rely on standards-compliant manifest/service worker and document browser-specific installation paths instead of forcing custom UX.
- **Maskable icons clipped in OS launchers:** generate dedicated maskable assets with safe-zone padding and validate them visually.
- **Unsaved work lost on update reload:** do not auto-reload; ask the user and reuse existing dirty-state protections where available.

## Open questions for enrichment

1. Should the manifest file be renamed from `site.webmanifest` to `manifest.webmanifest`, or kept as-is to minimize churn?
2. Should SDD Flow expose a visible "Install app" button in the authenticated shell, or rely only on browser install affordances for the first release?
3. Which automated PWA gate should be mandatory in CI: Lighthouse CI, Playwright-based checks, or a lightweight custom manifest/service-worker validator?
