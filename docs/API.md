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

## Academic — `/api/v1/academic` (academic module)

| Method | Path | Permission |
|---|---|---|
| GET/POST | `/classes` | `academic:read` / `academic:write` |
| GET/POST | `/subjects` | `academic:read` / `academic:write` |
| POST | `/enrollments` | `enrollments:write` |

## Attendance — `/api/v1/attendance` (attendance module)

| Method | Path | Permission | Notes |
|---|---|---|---|
| POST | `` | `attendance:write` | Record attendance (status validated). |
| GET | `/student/{id}/summary` | `attendance:read` | Attendance rate + counts. |

## Exams — `/api/v1/exams` (exams module)

| Method | Path | Permission | Notes |
|---|---|---|---|
| POST | `` | `exams:write` | Create an examination. |
| POST | `/marks` | `marks:write` | Record a mark (grade derived). |
| POST | `/report-cards/{exam}/{student}` | `reports:write` | Generate a report card from marks. |

## Finance — `/api/v1/finance` (billing module)

| Method | Path | Permission | Notes |
|---|---|---|---|
| POST | `/fees` | `finance:write` | Create a fee structure. |
| POST | `/invoices` | `finance:write` | Create an invoice. |
| POST | `/payments` | `finance:write` | Record a payment; balance/status recomputed. |
| GET | `/invoices/student/{id}` | `finance:read` | A student's invoices. |

## Payroll — `/api/v1/payroll` (payroll module)

| Method | Path | Permission | Notes |
|---|---|---|---|
| POST | `` | `payroll:write` | Compute a payslip (progressive PAYE). |
| GET | `/staff/{id}` | `payroll:read` | A staff member's payroll history. |

## Staff & HR — `/api/v1/staff` (hr_management module)

| Method | Path | Permission |
|---|---|---|
| GET/POST | `/staff` | `staff:read` / `staff:write` |
| POST | `/leaves` | `staff:read` |
| PATCH | `/leaves/{id}` | `staff:write` |

## Library — `/api/v1/library` (library module)

| Method | Path | Permission | Notes |
|---|---|---|---|
| GET/POST | `/books` | `library:read` / `library:write` | Catalog. |
| POST | `/loans` | `library:write` | Loan a book (decrements availability). |
| POST | `/loans/{id}/return` | `library:write` | Return a book. |

## Hostel — `/api/v1/hostel` (hostel module)

| Method | Path | Permission | Notes |
|---|---|---|---|
| GET/POST | `/rooms` | `hostel:read` / `hostel:write` | Rooms. |
| POST | `/allocations` | `hostel:write` | Allocate a room (capacity-checked). |

## Transport — `/api/v1/transport` (transport module)

| Method | Path | Permission |
|---|---|---|
| GET/POST | `/routes` | `transport:read` / `transport:write` |
| POST | `/assignments` | `transport:write` |

## E-Learning — `/api/v1/lms` (lms module)

| Method | Path | Permission |
|---|---|---|
| GET/POST | `/courses` | `lms:read` / `lms:write` |
| POST | `/lessons` | `lms:write` |

## Communication — `/api/v1/communication` (communication_hub / sms)

| Method | Path | Permission | Notes |
|---|---|---|---|
| POST | `/notifications` | `communication:write` | Send/queue; degrades to in-app if no SMS/email provider. |
| GET | `/notifications/{recipient}` | `communication:read` | Inbox. |

## Documents — `/api/v1/documents` (document_management module)

| Method | Path | Permission | Notes |
|---|---|---|---|
| GET/POST | `` | `documents:read` / `documents:write` | MIME/extension mismatch is rejected. |

## Reports — `/api/v1/reports`

| Method | Path | Permission | Notes |
|---|---|---|---|
| GET | `/finance/summary` | `reports:read` | Billed vs collected vs outstanding. |
| GET | `/students/count` | `reports:read` | Active student count. |
| GET | `/exams/{id}/ranking` | `reports:read` | Ranking from report-card averages. |

## AI — `/api/v1/ai` (ai_assistant module)

| Method | Path | Notes |
|---|---|---|
| GET | `/status` | Whether an AI provider is configured. |
| POST | `/report-comment` | Report-card comment; `ai_used` flags fallback. |
| POST | `/fee-reminder` | Fee-reminder message (always degrades gracefully). |

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
