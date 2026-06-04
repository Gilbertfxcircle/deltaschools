# Architecture Decision Records — Delta Plax Education Suite

This document records the key architectural decisions for the backend
foundation and why they were made.

---

## ADR-001: Schema-per-tenant isolation

**Decision.** Each school's data lives in its own PostgreSQL schema
(`school_{id}`); platform data lives in `deltaplax_global`. We do **not** use a
shared table with a `tenant_id` column.

**Why.** Strong blast-radius isolation, simpler per-tenant backup/restore, and
the ability to move a school to its own database later. It also matches the
offline model: a local EXE is effectively a single tenant.

**How isolation is enforced.**
- `app/core/tenant.py` turns an untrusted tenant identifier (subdomain, header,
  or JWT claim) into a **validated** schema name. Validation is a strict
  allowlist regex; anything that could break out of an identifier is rejected.
- `app/db/session.py::tenant_session` opens a session and immediately pins it
  with `SET search_path TO "school_x", "deltaplax_global"`. The schema string
  can never contain untrusted input because it is produced and re-validated by
  `schema_for_tenant` / `search_path_sql`.
- Tested in `tests/test_tenant_isolation.py`, including a battery of malicious
  tenant ids that must all be rejected.

**Trade-off.** Schema-per-tenant does not scale to millions of tenants the way
row-level isolation does; for the target market (hundreds–thousands of schools)
this is the right balance of isolation and operability.

---

## ADR-002: Pure domain core, framework-independent

**Decision.** The security/architecture "laws" live in modules with **zero
third-party imports**: `app/core/{tenant,rbac,modules,audit,security_policy,
response}.py` and `app/domain/approvals.py`.

**Why.** These rules are the parts we cannot afford to get wrong. Keeping them
free of FastAPI/SQLAlchemy means they are trivially unit-testable, fast, and
reusable by both the cloud server and the offline server. The web/DB layer is a
thin adapter over this core.

**Consequence.** The full test suite for the laws runs with only the Python
standard library (`python -m unittest`), which is also how they were validated
in a network-restricted environment.

---

## ADR-003: Immutable audit log, defense in depth

**Decision.** Audit records cannot be updated or deleted. Immutability is
enforced at three layers:

1. **Database trigger** — `BEFORE UPDATE OR DELETE` raises. Implemented for
   PostgreSQL (PL/pgSQL `RAISE EXCEPTION`) in migration `0001` and for SQLite
   (`RAISE(ABORT)`) in both the migration and `app/db/provisioning.py`, so the
   offline EXE is equally protected.
2. **ORM/service layer** — no update/delete path is exposed for audit models;
   the `/audit` API is read-only.
3. **Domain object** — `AuditRecord` is a frozen dataclass; mutation raises
   `FrozenInstanceError`.

**Tested by** `tests/test_audit_immutable.py` (object-level) and
`tests/test_audit_trigger_sqlite.py` (a real SQLite DB rejecting UPDATE/DELETE).

---

## ADR-004: Super Admin is pre-created, least-privileged

**Decision.** The Delta Plax Super Admin is created **only** by
`scripts/bootstrap_superadmin.py` (idempotent, password from environment). There
is no public registration endpoint. The Super Admin can manage institutions,
modules and subscriptions but is **forbidden** from writing student records,
marks, payments or payroll.

**Why.** The platform owner must be able to operate the platform without being
able to silently alter a school's protected records. To change protected data,
the Super Admin files an **approval request** that the School Director must
approve; the request and its outcome are both audited.

**Enforced by** `app/core/rbac.py` (`assert_super_admin_grant_is_safe` rejects
forbidden permissions, including wildcards that would imply them) and the
approval state machine in `app/domain/approvals.py`. Tested in
`tests/test_rbac.py` and `tests/test_approvals.py`.

---

## ADR-005: Offline-first, one codebase, two databases

**Decision.** The same application runs against PostgreSQL (cloud) and SQLite
(local EXE). `Settings.is_sqlite` switches behaviour where the two differ
(schemas, `search_path`, connection args). A `sync_queue` table records every
local write for later push; the Sync Engine (planned) reconciles with the cloud
and never silently overwrites — conflicts go through the same approval workflow.

**Why.** Connectivity in the target markets is intermittent. Offline operation
is a core requirement, not an add-on.

---

## ADR-006: Consistent response envelope + module gating

- Every API response uses `{ success, data, message, errors }`
  (`app/core/response.py`), including error handlers in `app/main.py`.
- The frontend renders navigation strictly from the institution's enabled
  modules (`/api/v1/modules/enabled`). Disabled modules are **absent** from the
  payload — never greyed out. Gating helper and tests:
  `app/core/modules.py`, `tests/test_modules.py`.

---

## Component map

```
Request → Nginx (subdomain → X-Tenant-ID)
        → TenantMiddleware (resolve + validate tenant, attach schema)
        → Route + RBAC dependency (require_permission / require_super_admin)
        → tenant_session (SET search_path) / global_session
        → SQLAlchemy models
        → audit service writes immutable record
        → response envelope
```
