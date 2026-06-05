// Resolve the current tenant on the client side. Priority:
//   1. The subdomain (stmarys.deltaplax.com -> "stmarys")
//   2. VITE_DEFAULT_TENANT (local dev convenience)
// Reserved/platform subdomains resolve to null (no tenant) so the admin and
// apex hosts are not treated as schools.

const RESERVED = new Set([
  "www",
  "admin",
  "api",
  "app",
  "static",
  "assets",
  "deltaplax",
  "localhost",
]);

export function tenantFromHostname(hostname: string): string | null {
  const host = hostname.split(":")[0]?.toLowerCase() ?? "";
  // Bare localhost / IP addresses have no subdomain tenant.
  if (!host || host === "localhost" || /^\d{1,3}(\.\d{1,3}){3}$/.test(host)) {
    return null;
  }
  const parts = host.split(".");
  // Need at least <tenant>.<root>.<tld> to have a tenant label.
  if (parts.length < 3) {
    return null;
  }
  const label = parts[0];
  if (!label || RESERVED.has(label)) {
    return null;
  }
  return label;
}

export function resolveTenant(): string | null {
  const fromHost =
    typeof window !== "undefined" ? tenantFromHostname(window.location.hostname) : null;
  if (fromHost) {
    return fromHost;
  }
  const fallback = import.meta.env.VITE_DEFAULT_TENANT;
  return fallback && fallback.length > 0 ? fallback : null;
}
