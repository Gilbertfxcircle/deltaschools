# Delta Plax Education Suite - Frontend

React 18 + TypeScript + Vite SPA. State via Zustand, styling via Tailwind.

## Highlights

- **Tenant-aware API client** (`src/api/client.ts`): attaches the JWT bearer
  token and `X-Tenant-ID` on every request, and transparently refreshes the
  access token on a 401 (single-flight).
- **Per-tenant branding** (`src/branding/applyBranding.ts`): applies a school's
  colors/logo via CSS custom properties and **resets defaults first** so one
  school's theme never leaks into another's (unit-tested).
- **Module-driven navigation** (`src/nav/navConfig.ts`): nav and feature routes
  render strictly from `/api/v1/modules/enabled` and the user's permissions.
  Disabled modules are absent entirely - no greyed-out links.
- **RBAC route guards** (`src/components/ProtectedRoute.tsx`) mirror the backend
  permission rule; the server still re-checks every request.
- **Login with MFA** (`src/pages/LoginPage.tsx`): two-step TOTP flow and
  lockout-aware error messaging.

## Develop

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000 (proxies /api -> http://localhost:8000)
```

## Build & test

```bash
npm run build      # tsc -b && vite build  -> dist/
npm run test       # vitest (envelope, nav gating, branding isolation, RBAC, tenant)
npm run typecheck  # tsc --noEmit (strict, no `any`)
```

## Environment

Copy `.env.example` to `.env`. The tenant is normally derived from the subdomain
(`stmarys.deltaplax.com`); set `VITE_DEFAULT_TENANT` to test a tenant locally.

> Note: this package was authored in an environment without npm registry access,
> so dependencies were not installed/run here. `npm install` then the scripts
> above will build and test it.
