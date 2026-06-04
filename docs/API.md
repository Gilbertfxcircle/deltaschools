# API Reference — Delta Plax Education Suite

All endpoints are versioned under `/api/v1`. Interactive docs are served at
`/docs` (Swagger UI) and the OpenAPI schema at `/openapi.json`.

## Conventions

- **Response envelope** (every response):
  ```json
  { "success": true, "data": { }, "message": "OK", "errors": [] }
  ```
- **Auth**: `Authorization: Bearer <access_token>`. Access tokens expire in
  15 minutes; use `/auth/refresh` with a refresh token (7 days).
- **Tenant**: resolved from the subdomain (`stmarys.deltaplax.com`), the
  `X-Tenant-ID` header, or the JWT `tenant` claim. Platform routes (`/auth`,
  `/admin`, `/institutions`) do not require a tenant.
- **RBAC**: routes are guarded by a required permission; `403` if missing.

---

## Auth — `/api/v1/auth`

| Method | Path | Body | Notes |
|---|---|---|---|
| POST | `/login` | `{ email, password, totp_code? }` | Enforces 5-fail/15-min lockout; TOTP required for roles L1–L5 when enabled. Returns access + refresh tokens. |
| POST | `/refresh` | `refresh_token` | Returns a new access token. |
| POST | `/logout` | — | Auth required. |

**Login example**
```bash
curl -X POST https://demo.deltaplax.com/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"director@demo.deltaplax.com","password":"Director#2026"}'
```

---

## Institutions — `/api/v1/institutions` (Super Admin)

| Method | Path | Notes |
|---|---|---|
| POST | `` | Create a school. Body: `{ tenant_id, name, institution_type, country }`. |
| GET | `` | List institutions. |
| GET | `/branding` | Per-tenant branding for the frontend (section 11). Never leaks across tenants. |

---

## Modules — `/api/v1/modules`

| Method | Path | Notes |
|---|---|---|
| GET | `/available` | Canonical list of 18 module keys. |
| GET | `/enabled` | Modules enabled for the current tenant (drives nav). |
| POST | `/{tenant_id}/{module_key}/enable` | Super Admin enables a module. |

---

## Approvals — `/api/v1/approvals`

The protected-data change flow (section 4.4).

| Method | Path | Permission | Notes |
|---|---|---|---|
| POST | `` | `approval_requests:submit` | Super Admin requests a change to protected data (`students`, `marks`, `payments`, `payroll`, …). |
| PATCH | `/{request_id}` | `approvals:decide` | Director approves/rejects. Body: `{ decision: "approved"\|"rejected", notes? }`. |
| GET | `` | authenticated | List requests for the caller's tenant. |

A change is applied **only** after approval; rejected/pending changes can never
be applied. Every step is written to the immutable audit log.

---

## Students — `/api/v1/students` (tenant-scoped)

| Method | Path | Permission | Notes |
|---|---|---|---|
| GET | `` | `students:read` | Lists students for the current tenant only. |
| POST | `` | `students:write` | Creates a student; `national_id` is AES-256 encrypted at rest. |

---

## Audit — `/api/v1/audit` (read-only)

| Method | Path | Permission | Notes |
|---|---|---|---|
| GET | `` | `audit:read` | Recent audit entries for the current tenant. There is **no** create/update/delete route — audit records are immutable. |

---

## Platform

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | Liveness probe used by orchestrators and the Sync Engine. |

---

## Error responses

Errors use the same envelope with `success: false`, e.g. a missing permission:

```json
{ "success": false, "data": null, "message": "Missing required permission: students:write", "errors": [] }
```

| Status | Meaning |
|---|---|
| 400 | Tenant not identified / bad input |
| 401 | Invalid/expired token, failed login, MFA required |
| 403 | Authenticated but missing permission |
| 422 | Request validation error (`errors` lists the fields) |
| 429 | Account locked (too many failed logins) |
