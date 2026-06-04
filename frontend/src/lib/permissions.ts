// Client mirror of the backend RBAC matching rule (app/core/rbac.py). Used for
// nav gating and route guards. The server remains the source of truth and
// re-checks every request; this only controls what the UI offers.

const WILDCARD = "*";

function matches(granted: string, required: string): boolean {
  if (granted === WILDCARD || granted === required) {
    return true;
  }
  if (granted.endsWith(":*")) {
    return required.startsWith(granted.slice(0, -1)); // keep trailing ':'
  }
  return false;
}

export function hasPermission(granted: readonly string[], required: string): boolean {
  return granted.some((g) => matches(g, required));
}
