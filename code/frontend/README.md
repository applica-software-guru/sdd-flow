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
- `npm run build` — typecheck and production build
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

## Bundle strategy

All route modules are lazy-loaded. The production entry chunk is approximately 240 kB minified (below the 500 kB target). Mermaid and Markdown rendering still produce larger lazy chunks; these are deliberate route-level exceptions and are not downloaded by landing, authentication or dashboard routes.

## Adding shadcn primitives

Run `npx shadcn@latest add <component>` from this directory. Review generated code, keep only primitives that are used, and compose product behaviour outside `components/ui/`.
