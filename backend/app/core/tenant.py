"""Tenant isolation primitives (schema-per-tenant).

LAW #1 from the brief: *Tenant isolation is law.* Every DB query must execute
within the correct PostgreSQL schema. This module is the single source of truth
for turning an untrusted tenant identifier (from a subdomain or JWT claim) into a
**validated** schema name that is safe to use in a ``SET search_path`` statement.

It contains NO third-party imports so it can be unit-tested in isolation and
reused by both the cloud server and the offline local server.
"""

from __future__ import annotations

import re

#: Schema that holds platform-wide (Delta Plax) tables.
GLOBAL_SCHEMA = "deltaplax_global"

#: Prefix applied to every per-school schema, e.g. ``school_001``.
SCHEMA_PREFIX = "school_"

# A tenant id is the subdomain label (``stmarys`` in ``stmarys.deltaplax.com``)
# or the numeric institution id (``001``). We accept lowercase alphanumerics,
# hyphens and underscores. Hyphens are converted to underscores for the schema.
_TENANT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,38}[a-z0-9]$|^[a-z0-9]$")

# PostgreSQL identifiers are capped at 63 bytes. We validate the *final* schema
# name against this strict allowlist before it can ever touch a SQL statement.
_SCHEMA_NAME_RE = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")

# Subdomains that are never tenants (reserved for the platform itself).
RESERVED_SUBDOMAINS = frozenset(
    {"www", "admin", "api", "app", "static", "assets", "deltaplax", "mail", "status"}
)


class TenantError(ValueError):
    """Raised when a tenant identifier or schema name is invalid/unsafe."""


def normalize_tenant_id(raw: str | None) -> str:
    """Validate and canonicalize an untrusted tenant identifier.

    Args:
        raw: The raw value from the ``X-Tenant-ID`` header, subdomain or JWT.

    Returns:
        The canonical, lowercased tenant id.

    Raises:
        TenantError: If the value is missing, reserved, or malformed.
    """
    if raw is None:
        raise TenantError("Tenant not identified")
    candidate = raw.strip().lower()
    if not candidate:
        raise TenantError("Tenant not identified")
    if candidate in RESERVED_SUBDOMAINS:
        raise TenantError(f"'{candidate}' is a reserved subdomain, not a tenant")
    if not _TENANT_ID_RE.match(candidate):
        raise TenantError(f"Malformed tenant id: {raw!r}")
    return candidate


def schema_for_tenant(raw_tenant_id: str | None) -> str:
    """Return the validated schema name for a tenant id.

    Hyphens in the tenant id are converted to underscores so the resulting
    schema name is a legal SQL identifier. The result is validated against a
    strict allowlist before being returned, guaranteeing it is injection-safe.

    Raises:
        TenantError: If the resulting schema name is not a safe identifier.
    """
    tenant_id = normalize_tenant_id(raw_tenant_id)
    schema = SCHEMA_PREFIX + tenant_id.replace("-", "_")
    if not is_safe_schema_name(schema):
        raise TenantError(f"Refusing unsafe schema name derived from {raw_tenant_id!r}")
    return schema


def is_safe_schema_name(name: str) -> bool:
    """True only if ``name`` is a legal, injection-safe PostgreSQL identifier."""
    return bool(_SCHEMA_NAME_RE.match(name))


def search_path_sql(schema: str) -> str:
    """Build a ``SET search_path`` statement for a *validated* schema.

    The schema is re-validated here as defense-in-depth: this function refuses
    to construct SQL for any name that is not on the strict allowlist. Callers
    should still pass schemas produced by :func:`schema_for_tenant`.

    Raises:
        TenantError: If ``schema`` fails validation.
    """
    if not is_safe_schema_name(schema):
        raise TenantError(f"Unsafe schema name: {schema!r}")
    # The global schema is always included last so shared sequences/extensions
    # remain reachable, while tenant tables take precedence.
    return f'SET search_path TO "{schema}", "{GLOBAL_SCHEMA}"'


def tenant_from_host(host: str | None, root_domain: str) -> str | None:
    """Extract a tenant id from a request Host header, if present.

    ``stmarys.deltaplax.com`` -> ``stmarys``. Returns ``None`` when the host is
    the bare root domain or a reserved subdomain (e.g. ``admin.deltaplax.com``).
    """
    if not host:
        return None
    hostname = host.split(":", 1)[0].strip().lower()  # drop any :port
    root = root_domain.strip().lower()
    if hostname == root or not hostname.endswith("." + root):
        return None
    label = hostname[: -(len(root) + 1)]  # text before ".<root>"
    # Only the left-most label is the tenant (ignore deeper nesting).
    label = label.split(".")[-1]
    if label in RESERVED_SUBDOMAINS:
        return None
    try:
        return normalize_tenant_id(label)
    except TenantError:
        return None
