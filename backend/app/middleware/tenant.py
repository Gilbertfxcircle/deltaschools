"""Tenant resolution middleware (section 8.2).

Resolves the tenant for each request - in priority order:

1. The ``X-Tenant-ID`` header set by Nginx from the subdomain (section 8.1).
2. The request ``Host`` header (``stmarys.deltaplax.com`` -> ``stmarys``).
3. The ``tenant`` claim inside the JWT.

The resolved, validated tenant id and schema are stashed on ``request.state``.
Platform/admin routes do not require a tenant and are allowlisted.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.response import fail
from app.core.security import decode_token
from app.core.tenant import TenantError, schema_for_tenant, tenant_from_host

_settings = get_settings()

# Routes that operate on the global schema and therefore need no tenant.
_TENANTLESS_PREFIXES = (
    f"{_settings.api_v1_prefix}/admin",
    f"{_settings.api_v1_prefix}/institutions",
    f"{_settings.api_v1_prefix}/auth",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
)


def _tenant_from_jwt(request: Request) -> str | None:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    try:
        payload = decode_token(auth.split(" ", 1)[1])
    except Exception:
        return None
    return payload.get("tenant")


class TenantMiddleware(BaseHTTPMiddleware):
    """Attach ``request.state.tenant_id`` / ``tenant_schema`` to each request."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        path = request.url.path
        is_tenantless = any(path.startswith(p) for p in _TENANTLESS_PREFIXES)

        raw_tenant = (
            request.headers.get("X-Tenant-ID")
            or tenant_from_host(request.headers.get("host"), _settings.root_domain)
            or _tenant_from_jwt(request)
        )

        if raw_tenant is None:
            request.state.tenant_id = None
            request.state.tenant_schema = None
            if is_tenantless:
                return await call_next(request)
            return JSONResponse(fail("Tenant not identified"), status_code=400)

        try:
            request.state.tenant_id = raw_tenant
            request.state.tenant_schema = schema_for_tenant(raw_tenant)
        except TenantError as exc:
            return JSONResponse(fail(str(exc)), status_code=400)

        return await call_next(request)
