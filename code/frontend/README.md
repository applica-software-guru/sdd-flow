# SDD Flow frontend

React 18 + Vite + TypeScript, Tailwind CSS, code-owned shadcn/ui primitives and TanStack Query.

## Commands

Use npm scripts directly or `./cli.sh <command>`:

- `npm run dev` — development server
- `npm run lint` / `npm run lint:fix` — type-aware ESLint
- `npm run typecheck` — TypeScript project references
- `npm run format` / `npm run format:check` — Prettier and Tailwind class ordering
- `npm test` — Vitest
- `npm run test:e2e` — Playwright
- `npm run build` — typecheck, production build and generated PWA artifact validation
- `npm run check:pwa` — validate manifest metadata and public icon dimensions
- `npm run check` — complete CI quality gate

## Structure

- `src/components/ui/`: shadcn primitives owned by this repository
- `src/components/shared/`: reusable product-level UI
- `src/components/layout/`: app-shell components
- `src/features/`: domain-focused shared workflows
- `src/hooks/`: React Query adapters consumed by components
- `src/api/`: query keys and typed transport helpers
- `src/pages/`: thin route composition modules

All application source filenames must use kebab-case. Run `npm run check:filenames` to validate.

## PWA development

Production builds generate and register the installable PWA service worker. Development mode keeps service-worker registration disabled so stale caches do not mask frontend changes.

If an old local service worker affects testing, clear it from the browser developer tools under Application → Service Workers, then clear site storage and reload. API, authentication, websocket and worker traffic must remain network-backed; do not add stale-cache fallbacks for protected server data.

Run `npm run check:pwa` after changing `index.html`, `public/site.webmanifest` or app icons. `npm run build` also validates the generated `dist/sw.js` artifact.

## Bundle strategy

All route modules are lazy-loaded. The production entry chunk is approximately 240 kB minified (below the 500 kB target). Mermaid and Markdown rendering still produce larger lazy chunks; these are deliberate route-level exceptions and are not downloaded by landing, authentication or dashboard routes.

## Adding shadcn primitives

Run `npx shadcn@latest add <component>` from this directory. Review generated code, keep only primitives that are used, and compose product behaviour outside `components/ui/`.
